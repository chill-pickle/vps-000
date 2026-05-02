from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

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
# Model
# ---------------------------------------------------------------------------


class Story(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    status: Status = Status.todo
    priority: Priority = Priority.medium
    assignee: Optional[str] = None
    requested_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class StoryCreate(SQLModel):
    title: str
    description: Optional[str] = None
    status: Status = Status.todo
    priority: Priority = Priority.medium
    assignee: Optional[str] = None
    requested_by: Optional[str] = None


class StoryUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    assignee: Optional[str] = None
    requested_by: Optional[str] = None


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

import os

os.makedirs("data", exist_ok=True)
DB_URL = "sqlite:///data/todo.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)
    # Enable WAL mode for better concurrent access
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Stories Tracker API", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stories", response_model=list[Story])
def list_stories(
    status: Optional[Status] = Query(None),
    priority: Optional[Priority] = Query(None),
    assignee: Optional[str] = Query(None),
    requested_by: Optional[str] = Query(None),
):
    with Session(engine) as session:
        query = select(Story)
        if status:
            query = query.where(Story.status == status)
        if priority:
            query = query.where(Story.priority == priority)
        if assignee:
            query = query.where(Story.assignee == assignee)
        if requested_by:
            query = query.where(Story.requested_by == requested_by)
        return session.exec(query.order_by(Story.id.desc())).all()


@app.post("/stories", response_model=Story, status_code=201)
def create_story(body: StoryCreate):
    story = Story(**body.model_dump())
    with Session(engine) as session:
        session.add(story)
        session.commit()
        session.refresh(story)
        return story


@app.patch("/stories/{story_id}", response_model=Story)
def update_story(story_id: int, body: StoryUpdate):
    with Session(engine) as session:
        story = session.get(Story, story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        updates = body.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(story, key, value)
        story.updated_at = datetime.now(timezone.utc)
        session.add(story)
        session.commit()
        session.refresh(story)
        return story


@app.delete("/stories/{story_id}", status_code=204)
def delete_story(story_id: int):
    with Session(engine) as session:
        story = session.get(Story, story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        session.delete(story)
        session.commit()
