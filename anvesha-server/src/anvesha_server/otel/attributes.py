from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from openinference.semconv.trace import DocumentAttributes, SpanAttributes

JSON_STRING_ATTRIBUTES = (
    DocumentAttributes.DOCUMENT_METADATA,
    SpanAttributes.LLM_PROMPT_TEMPLATE_VARIABLES,
    SpanAttributes.METADATA,
    SpanAttributes.TOOL_PARAMETERS,
)


def load_json_strings(key_values: Iterable[tuple[str, Any]]) -> list[tuple[str, Any]]:
    decoded: list[tuple[str, Any]] = []
    for key, value in key_values:
        if key in JSON_STRING_ATTRIBUTES and isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        decoded.append((key, value))
    return decoded


def unflatten(key_value_pairs: Iterable[tuple[str, Any]], separator: str = ".") -> dict[str, Any]:
    root: dict[str, Any] = {}
    for key, value in key_value_pairs:
        if value is None:
            continue
        parts = [part.strip() for part in key.split(separator) if part.strip()]
        if not parts:
            continue
        cursor = root
        for part in parts[:-1]:
            current = cursor.get(part)
            if not isinstance(current, dict):
                current = {}
                cursor[part] = current
            cursor = current
        cursor[parts[-1]] = value
    return root


def get_attribute_value(
    attributes: Mapping[str, Any] | None,
    key: str | Sequence[str],
    separator: str = ".",
) -> Any | None:
    if not isinstance(attributes, Mapping):
        return None

    path: list[str] = []
    if isinstance(key, str):
        path.extend(key.split(separator))
    else:
        for segment in key:
            path.extend(segment.split(separator))

    cursor: Any = attributes
    for part in path:
        if not isinstance(cursor, Mapping) or part not in cursor:
            return None
        cursor = cursor[part]
    return cursor
