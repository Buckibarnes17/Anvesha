from __future__ import annotations

import json
from binascii import hexlify
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

import opentelemetry.proto.trace.v1.trace_pb2 as otlp
from openinference.semconv.resource import ResourceAttributes
from openinference.semconv.trace import OpenInferenceMimeTypeValues, SpanAttributes
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue

from .attributes import get_attribute_value, load_json_strings, unflatten
from .schemas import Span, SpanContext, SpanEvent, SpanKind, SpanStatusCode

OPENINFERENCE_SPAN_KIND = SpanAttributes.OPENINFERENCE_SPAN_KIND
INPUT_MIME_TYPE = SpanAttributes.INPUT_MIME_TYPE
INPUT_VALUE = SpanAttributes.INPUT_VALUE
OUTPUT_MIME_TYPE = SpanAttributes.OUTPUT_MIME_TYPE
OUTPUT_VALUE = SpanAttributes.OUTPUT_VALUE


def get_project_name(resource_attributes: Iterable[KeyValue], default_project_name: str) -> str:
    for key_value in resource_attributes:
        if key_value.key == ResourceAttributes.PROJECT_NAME and key_value.value.string_value:
            return str(key_value.value.string_value)
    return default_project_name


def decode_otlp_span(otlp_span: otlp.Span) -> Span:
    attributes = unflatten(load_json_strings(_decode_key_values(otlp_span.attributes)))
    span_kind = SpanKind(get_attribute_value(attributes, OPENINFERENCE_SPAN_KIND) or "UNKNOWN")
    events = [_decode_event(event) for event in otlp_span.events]
    _normalize_io_payload(attributes, "input", INPUT_VALUE, INPUT_MIME_TYPE)
    _normalize_io_payload(attributes, "output", OUTPUT_VALUE, OUTPUT_MIME_TYPE)

    return Span(
        name=otlp_span.name,
        context=SpanContext(
            trace_id=_decode_identifier(otlp_span.trace_id) or "",
            span_id=_decode_identifier(otlp_span.span_id) or "",
        ),
        parent_id=_decode_identifier(otlp_span.parent_span_id),
        start_time=_decode_unix_nano(otlp_span.start_time_unix_nano),
        end_time=_decode_unix_nano(otlp_span.end_time_unix_nano),
        status_code=_decode_status_code(otlp_span.status),
        status_message=otlp_span.status.message,
        attributes=attributes,
        events=events,
        span_kind=span_kind,
    )


def _normalize_io_payload(
    attributes: dict[str, Any],
    root_key: str,
    value_key: str,
    mime_type_key: str,
) -> None:
    value = get_attribute_value(attributes, value_key)
    if value is None or isinstance(value, str):
        return
    node = attributes.get(root_key)
    if not isinstance(node, dict):
        node = {}
        attributes[root_key] = node
    node["value"] = json.dumps(value)
    node["mime_type"] = OpenInferenceMimeTypeValues.JSON.value
    if get_attribute_value(attributes, mime_type_key) is None:
        node.setdefault("mime_type", OpenInferenceMimeTypeValues.JSON.value)


def _decode_identifier(identifier: bytes) -> str | None:
    if not identifier:
        return None
    return hexlify(identifier).decode()


def _decode_unix_nano(unix_nano: int) -> datetime:
    return datetime.fromtimestamp(unix_nano / 1e9, tz=timezone.utc)


def _decode_event(otlp_event: otlp.Span.Event) -> SpanEvent:
    return SpanEvent(
        name=otlp_event.name,
        timestamp=_decode_unix_nano(otlp_event.time_unix_nano),
        attributes=dict(_decode_key_values(otlp_event.attributes)),
    )


def _decode_key_values(key_values: Iterable[KeyValue]) -> list[tuple[str, Any]]:
    return [(key_value.key, _decode_value(key_value.value)) for key_value in key_values]


def _decode_value(any_value: AnyValue) -> Any:
    which = any_value.WhichOneof("value")
    if which == "string_value":
        return any_value.string_value
    if which == "bool_value":
        return any_value.bool_value
    if which == "int_value":
        return any_value.int_value
    if which == "double_value":
        return any_value.double_value
    if which == "array_value":
        return [_decode_value(item) for item in any_value.array_value.values]
    if which == "kvlist_value":
        return dict(_decode_key_values(any_value.kvlist_value.values))
    if which == "bytes_value":
        return any_value.bytes_value.hex()
    return None


def _decode_status_code(status: otlp.Status) -> SpanStatusCode:
    mapping = {
        otlp.Status.StatusCode.STATUS_CODE_UNSET: SpanStatusCode.UNSET,
        otlp.Status.StatusCode.STATUS_CODE_OK: SpanStatusCode.OK,
        otlp.Status.StatusCode.STATUS_CODE_ERROR: SpanStatusCode.ERROR,
    }
    return mapping.get(status.code, SpanStatusCode.UNSET)
