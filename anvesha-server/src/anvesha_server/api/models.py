from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    name: str
    traceCount: int
    spanCount: int
    lastUpdatedAt: datetime | None


class TraceSummary(BaseModel):
    traceId: str
    projectName: str
    sessionId: str | None
    startTime: datetime
    endTime: datetime
    latencyMs: float
    spanCount: int


class SpanEventModel(BaseModel):
    name: str
    timestamp: datetime
    attributes: dict[str, Any]


class SpanDetail(BaseModel):
    traceId: str
    spanId: str
    parentId: str | None
    name: str
    spanKind: str
    statusCode: str
    statusMessage: str
    startTime: datetime
    endTime: datetime
    latencyMs: float
    attributes: dict[str, Any]
    events: list[SpanEventModel]


class TraceDetail(BaseModel):
    traceId: str
    projectName: str
    sessionId: str | None
    startTime: datetime
    endTime: datetime
    latencyMs: float
    spanCount: int
    spans: list[SpanDetail]
