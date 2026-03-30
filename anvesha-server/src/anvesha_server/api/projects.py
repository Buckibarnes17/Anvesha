from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from anvesha_server.db.engine import get_session
from anvesha_server.db.models import Project, Span, Trace

from .models import ProjectSummary

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
async def list_projects(session: AsyncSession = Depends(get_session)) -> list[ProjectSummary]:
    stmt = (
        select(
            Project.name,
            func.count(sa.distinct(Trace.id)).label("trace_count"),
            func.count(Span.id).label("span_count"),
            func.max(Trace.end_time).label("last_updated_at"),
        )
        .select_from(Project)
        .outerjoin(Trace, Trace.project_rowid == Project.id)
        .outerjoin(Span, Span.trace_rowid == Trace.id)
        .group_by(Project.id)
        .order_by(Project.name.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        ProjectSummary(
            name=row.name,
            traceCount=int(row.trace_count or 0),
            spanCount=int(row.span_count or 0),
            lastUpdatedAt=row.last_updated_at,
        )
        for row in rows
    ]
