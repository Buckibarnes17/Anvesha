from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    traces: Mapped[list["Trace"]] = relationship(back_populates="project")
    sessions: Mapped[list["ProjectSession"]] = relationship(back_populates="project")


class ProjectSession(Base, TimestampMixin):
    __tablename__ = "project_sessions"
    __table_args__ = (
        UniqueConstraint("project_id", "session_id", name="uq_project_sessions_project_session_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    project: Mapped[Project] = relationship(back_populates="sessions")
    traces: Mapped[list["Trace"]] = relationship(back_populates="project_session")

    @property
    def latency_ms(self) -> float:
        return (self.end_time - self.start_time).total_seconds() * 1000.0


class Trace(Base, TimestampMixin):
    __tablename__ = "traces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    project_rowid: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    project_session_rowid: Mapped[int | None] = mapped_column(
        ForeignKey("project_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    project: Mapped[Project] = relationship(back_populates="traces")
    project_session: Mapped[ProjectSession | None] = relationship(back_populates="traces")
    spans: Mapped[list["Span"]] = relationship(back_populates="trace")

    @property
    def latency_ms(self) -> float:
        return (self.end_time - self.start_time).total_seconds() * 1000.0


class Span(Base, TimestampMixin):
    __tablename__ = "spans"
    __table_args__ = (
        UniqueConstraint("trace_rowid", "span_id", name="uq_spans_trace_span_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trace_rowid: Mapped[int] = mapped_column(ForeignKey("traces.id", ondelete="CASCADE"), index=True)
    span_id: Mapped[str] = mapped_column(String(16), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    span_kind: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(512), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    status_code: Mapped[str] = mapped_column(String(32), default="UNSET")
    status_message: Mapped[str] = mapped_column(Text, default="")

    trace: Mapped[Trace] = relationship(back_populates="spans")

    @property
    def latency_ms(self) -> float:
        return (self.end_time - self.start_time).total_seconds() * 1000.0
