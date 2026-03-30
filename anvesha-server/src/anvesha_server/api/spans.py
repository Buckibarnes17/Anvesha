from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from anvesha_server.db.engine import get_session
from anvesha_server.db.models import Span

from .common import serialize_span
from .models import SpanDetail

router = APIRouter(tags=["spans"])


@router.get("/spans/{span_id}", response_model=SpanDetail)
async def get_span(span_id: str, session: AsyncSession = Depends(get_session)) -> SpanDetail:
    span = await session.scalar(
        select(Span)
        .options(selectinload(Span.trace))
        .where(Span.span_id == span_id)
    )
    if span is None:
        raise HTTPException(status_code=404, detail=f"Span '{span_id}' was not found")
    return serialize_span(span)
