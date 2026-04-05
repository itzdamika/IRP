from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255), default="")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    threads: Mapped[list["Thread"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    settings_row: Mapped["UserSettingsRow | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserSettingsRow(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    pass_threshold: Mapped[float] = mapped_column(default=9.0)
    max_planning_rounds: Mapped[int] = mapped_column(default=10)
    max_requirement_hops: Mapped[int] = mapped_column(default=12)
    report_depth: Mapped[str] = mapped_column(String(32), default="extreme")
    thinking_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    show_internal_panels: Mapped[bool] = mapped_column(Boolean, default=True)
    theme: Mapped[str] = mapped_column(String(32), default="dark")

    user: Mapped["User"] = relationship(back_populates="settings_row")


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(512), default="New chat")
    phase: Mapped[str] = mapped_column(String(32), default="REQUIREMENTS")
    active_branch_id: Mapped[str] = mapped_column(String(36), default=_uuid)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    engine_state_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="threads")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
    branches: Mapped[list["Branch"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )


class Branch(Base):
    """Conversation branch (main or fork). Engine state is stored per branch."""

    __tablename__ = "branches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    parent_branch_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    forked_from_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    label: Mapped[str] = mapped_column(String(256), default="main")
    engine_state_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    thread: Mapped["Thread"] = relationship(back_populates="branches")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text, default="")
    agent: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    thread: Mapped["Thread"] = relationship(back_populates="messages")


class ShareToken(Base):
    __tablename__ = "share_tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    branch_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ArtifactRecord(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    filename: Mapped[str] = mapped_column(String(512))
    path: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
