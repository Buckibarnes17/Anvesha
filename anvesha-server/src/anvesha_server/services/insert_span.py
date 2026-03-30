from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from openinference.semconv.trace import SpanAttributes

from anvesha_server.db.models import Project, ProjectSession, Span as SpanModel, Trace
from anvesha_server.otel.attributes import get_attribute_value
from anvesha_server.otel.schemas import Span


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


async def _get_or_create_project(session: AsyncSession, project_name: str) -> Project:
    project = await session.scalar(select(Project).where(Project.name == project_name))
    if project is None:
        project = Project(name=project_name)
        session.add(project)
        await session.flush()
    return project


async def insert_span(session: AsyncSession, span: Span, project_name: str) -> SpanModel | None:
    existing_span = await session.scalar(select(SpanModel).where(SpanModel.span_id == span.context.span_id))
    if existing_span is not None:
        return None

    span_start_time = _ensure_aware(span.start_time)
    span_end_time = _ensure_aware(span.end_time)

    trace = await session.scalar(select(Trace).where(Trace.trace_id == span.context.trace_id))
    if trace is None:
        project = await _get_or_create_project(session, project_name)
        trace = Trace(
            trace_id=span.context.trace_id,
            project_rowid=project.id,
            start_time=span_start_time,
            end_time=span_end_time,
        )
        session.add(trace)
        await session.flush()
    else:
        trace_start_time = _ensure_aware(trace.start_time)
        trace_end_time = _ensure_aware(trace.end_time)
        if span_start_time < trace_start_time:
            trace.start_time = span_start_time
            trace_start_time = span_start_time
        if trace_end_time < span_end_time:
            trace.end_time = span_end_time
            trace_end_time = span_end_time

    session_id_value = get_attribute_value(span.attributes, SpanAttributes.SESSION_ID)
    session_id = str(session_id_value).strip() if session_id_value is not None else ""
    if session_id:
        project_session = None
        if trace.project_session_rowid is not None:
            project_session = await session.get(ProjectSession, trace.project_session_rowid)
        if project_session is None:
            project_session = await session.scalar(
                select(ProjectSession).where(
                    ProjectSession.project_id == trace.project_rowid,
                    ProjectSession.session_id == session_id,
                )
            )
        if project_session is None:
            project_session = ProjectSession(
                project_id=trace.project_rowid,
                session_id=session_id,
                start_time=_ensure_aware(trace.start_time),
                end_time=_ensure_aware(trace.end_time),
            )
            session.add(project_session)
            await session.flush()
        else:
            session_start_time = _ensure_aware(project_session.start_time)
            session_end_time = _ensure_aware(project_session.end_time)
            trace_start_time = _ensure_aware(trace.start_time)
            trace_end_time = _ensure_aware(trace.end_time)
            if trace_start_time < session_start_time:
                project_session.start_time = trace_start_time
            if session_end_time < trace_end_time:
                project_session.end_time = trace_end_time
        trace.project_session_rowid = project_session.id

    row = SpanModel(
        trace_rowid=trace.id,
        span_id=span.context.span_id,
        parent_id=span.parent_id,
        span_kind=span.span_kind.value,
        name=span.name,
        start_time=span_start_time,
        end_time=span_end_time,
        attributes=dict(span.attributes),
        events=[
            {
                "name": event.name,
                "timestamp": _ensure_aware(event.timestamp).isoformat(),
                "attributes": dict(event.attributes),
            }
            for event in span.events
        ],
        status_code=span.status_code.value,
        status_message=span.status_message,
    )
    session.add(row)
    await session.flush()
    return row
