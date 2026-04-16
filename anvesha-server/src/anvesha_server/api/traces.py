from __future__ import annotations

import gzip
import zlib

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from google.protobuf.message import DecodeError
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
    ExportTraceServiceResponse,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from anvesha_server.config import get_settings
from anvesha_server.db.engine import get_session
from anvesha_server.db.models import Project, ProjectSession, Span, Trace
from anvesha_server.otel import decode_otlp_span, get_project_name
from anvesha_server.services import insert_span

from .common import get_project_or_404, serialize_span
from .models import TraceDetail, TraceSummary

router = APIRouter(tags=["traces"])
settings = get_settings()


@router.post("/traces", response_class=Response)
async def post_traces(
    request: Request,
    session: AsyncSession = Depends(get_session),
    content_type: str | None = Header(default=None),
    content_encoding: str | None = Header(default=None),
) -> Response:
    if not content_type or not content_type.startswith("application/x-protobuf"):
        raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}")
    if content_encoding and content_encoding not in {"gzip", "deflate"}:
        raise HTTPException(status_code=415, detail=f"Unsupported content encoding: {content_encoding}")

    body = await request.body()
    try:
        if content_encoding == "gzip":
            body = gzip.decompress(body)
        elif content_encoding == "deflate":
            body = zlib.decompress(body)
    except (OSError, zlib.error) as exc:
        raise HTTPException(status_code=422, detail="Request body is not valid compressed OTLP data") from exc

    export_request = ExportTraceServiceRequest()
    try:
        export_request.ParseFromString(body)
    except DecodeError as exc:
        raise HTTPException(status_code=422, detail="Request body is invalid ExportTraceServiceRequest") from exc

    for resource_spans in export_request.resource_spans:
        project_name = get_project_name(resource_spans.resource.attributes, settings.default_project_name)
        for scope_spans in resource_spans.scope_spans:
            for otlp_span in scope_spans.spans:
                try:
                    span = decode_otlp_span(otlp_span)
                    await insert_span(session, span, project_name)
                except ValueError as exc:
                    raise HTTPException(status_code=422, detail=str(exc)) from exc

    await session.commit()
    response_message = ExportTraceServiceResponse()
    return Response(content=response_message.SerializeToString(), media_type="application/x-protobuf")


@router.get("/projects/{project_name}/traces", response_model=list[TraceSummary])
async def list_project_traces(
    project_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> list[TraceSummary]:
    project = await get_project_or_404(session, project_name)
    stmt = (
        select(
            Trace,
            ProjectSession.session_id,
            func.count(Span.id).label("span_count"),
        )
        .outerjoin(ProjectSession, Trace.project_session_rowid == ProjectSession.id)
        .outerjoin(Span, Span.trace_rowid == Trace.id)
        .where(Trace.project_rowid == project.id)
        .group_by(Trace.id, ProjectSession.session_id)
        .order_by(Trace.start_time.desc(), Trace.id.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        TraceSummary(
            traceId=trace.trace_id,
            projectName=project.name,
            sessionId=session_id,
            startTime=trace.start_time,
            endTime=trace.end_time,
            latencyMs=trace.latency_ms,
            spanCount=int(span_count or 0),
        )
        for trace, session_id, span_count in rows
    ]


@router.get("/traces/{trace_id}", response_model=TraceDetail)
async def get_trace(trace_id: str, session: AsyncSession = Depends(get_session)) -> TraceDetail:
    trace_row = (
        await session.execute(
            select(Trace, Project.name, ProjectSession.session_id)
            .join(Project, Trace.project_rowid == Project.id)
            .outerjoin(ProjectSession, Trace.project_session_rowid == ProjectSession.id)
            .where(Trace.trace_id == trace_id)
        )
    ).first()
    if trace_row is None:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' was not found")

    trace, project_name, session_id = trace_row
    spans = (
        await session.scalars(
            select(Span)
            .where(Span.trace_rowid == trace.id)
            .order_by(Span.start_time.asc(), Span.id.asc())
        )
    ).all()

    return TraceDetail(
        traceId=trace.trace_id,
        projectName=project_name,
        sessionId=session_id,
        startTime=trace.start_time,
        endTime=trace.end_time,
        latencyMs=trace.latency_ms,
        spanCount=len(spans),
        spans=[serialize_span(span) for span in spans],
    )
