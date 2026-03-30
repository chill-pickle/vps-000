from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    text_lower: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    is_phrase: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="word", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False
    )
    translation: Mapped[str] = mapped_column(String, nullable=False)
    meaning: Mapped[str] = mapped_column(String, nullable=False)
    example_1: Mapped[str] = mapped_column(String, nullable=False)
    example_2: Mapped[str] = mapped_column(String, nullable=False)
    example_3: Mapped[str] = mapped_column(String, nullable=False)
    word_type: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="openai")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    word: Mapped["Word"] = relationship(back_populates="answers")
    votes: Mapped[list["Vote"]] = relationship(
        back_populates="answer", cascade="all, delete-orphan"
    )


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("answer_id", "browser_id", name="uq_vote_answer_browser"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    answer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    browser_id: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # +1 or -1
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    answer: Mapped["Answer"] = relationship(back_populates="votes")
