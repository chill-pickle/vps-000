from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

DB_PATH = "data/todo.db"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT,
            status      TEXT    NOT NULL DEFAULT 'todo',
            priority    TEXT    NOT NULL DEFAULT 'medium',
            assignee    TEXT,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Status = Status.todo
    priority: Priority = Priority.medium
    assignee: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    assignee: Optional[str] = None


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: Status
    priority: Priority
    assignee: Optional[str]
    created_at: datetime
    updated_at: datetime


def row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        status=Status(row["status"]),
        priority=Priority(row["priority"]),
        assignee=row["assignee"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os

    os.makedirs("data", exist_ok=True)
    init_db()
    yield


app = FastAPI(title="TODO API", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    status: Optional[Status] = Query(None),
    priority: Optional[Priority] = Query(None),
    assignee: Optional[str] = Query(None),
):
    conn = get_db()
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status.value)
    if priority:
        query += " AND priority = ?"
        params.append(priority.value)
    if assignee:
        query += " AND assignee = ?"
        params.append(assignee)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_task(r) for r in rows]


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(body: TaskCreate):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cur = conn.execute(
        """
        INSERT INTO tasks (title, description, status, priority, assignee, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            body.title,
            body.description,
            body.status.value,
            body.priority.value,
            body.assignee,
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return row_to_task(row)


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, body: TaskUpdate):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        conn.close()
        return row_to_task(row)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = [v.value if isinstance(v, Enum) else v for v in updates.values()]
    values.append(task_id)

    conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_db()
    result = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
