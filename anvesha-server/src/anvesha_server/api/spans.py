from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from anvesha_server.db.engine import get_session
from anvesha_server.db.models import Span, Trace

from .common import serialize_span
from .models import SpanDetail

router = APIRouter(tags=["spans"])


@router.get("/spans/{span_id}", response_model=SpanDetail)
async def get_span(
    span_id: str,
    trace_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> SpanDetail:
    stmt = (
        select(Span)
        .options(selectinload(Span.trace))
        .where(Span.span_id == span_id)
        .order_by(Span.id.asc())
        .limit(2)
    )
    if trace_id:
        stmt = (
            select(Span)
            .join(Trace, Span.trace_rowid == Trace.id)
            .options(selectinload(Span.trace))
            .where(
                Span.span_id == span_id,
                Trace.trace_id == trace_id,
            )
            .limit(1)
        )

    spans = (await session.scalars(stmt)).all()
    if not spans:
        raise HTTPException(status_code=404, detail=f"Span '{span_id}' was not found")
    if trace_id is None and len(spans) > 1:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Span '{span_id}' is not globally unique. "
                "Retry with the trace_id query parameter."
            ),
        )
    return serialize_span(spans[0])
