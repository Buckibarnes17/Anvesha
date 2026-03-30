from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class SpanStatusCode(Enum):
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"

    @classmethod
    def _missing_(cls, value: object) -> "SpanStatusCode" | None:
        if isinstance(value, str) and value:
            return cls(value.upper())
        return cls.UNSET


class SpanKind(Enum):
    TOOL = "TOOL"
    CHAIN = "CHAIN"
    LLM = "LLM"
    PROMPT = "PROMPT"
    RETRIEVER = "RETRIEVER"
    EMBEDDING = "EMBEDDING"
    AGENT = "AGENT"
    RERANKER = "RERANKER"
    EVALUATOR = "EVALUATOR"
    GUARDRAIL = "GUARDRAIL"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> "SpanKind" | None:
        if isinstance(value, str) and value:
            try:
                return cls(value.upper())
            except ValueError:
                return cls.UNKNOWN
        return cls.UNKNOWN


TraceID = str
SpanID = str


@dataclass(frozen=True)
class SpanContext:
    trace_id: TraceID
    span_id: SpanID


@dataclass(frozen=True)
class SpanEvent:
    name: str
    timestamp: datetime
    attributes: dict[str, Any]


@dataclass(frozen=True)
class Span:
    name: str
    context: SpanContext
    span_kind: SpanKind
    parent_id: SpanID | None
    start_time: datetime
    end_time: datetime
    status_code: SpanStatusCode
    status_message: str
    attributes: dict[str, Any]
    events: list[SpanEvent]
