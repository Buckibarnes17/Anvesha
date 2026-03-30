from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from anvesha_server.db.models import Project, Span as SpanModel

from .models import SpanDetail, SpanEventModel


async def get_project_or_404(session: AsyncSession, project_name: str) -> Project:
    project = await session.scalar(select(Project).where(Project.name == project_name))
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' was not found")
    return project


def _parse_event_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise ValueError(f"Unsupported event timestamp: {value!r}")


def serialize_span(span: SpanModel) -> SpanDetail:
    return SpanDetail(
        traceId=span.trace.trace_id,
        spanId=span.span_id,
        parentId=span.parent_id,
        name=span.name,
        spanKind=span.span_kind,
        statusCode=span.status_code,
        statusMessage=span.status_message,
        startTime=span.start_time,
        endTime=span.end_time,
        latencyMs=span.latency_ms,
        attributes=span.attributes or {},
        events=[
            SpanEventModel(
                name=event.get("name", ""),
                timestamp=_parse_event_timestamp(event.get("timestamp")),
                attributes=event.get("attributes") or {},
            )
            for event in (span.events or [])
        ],
    )
