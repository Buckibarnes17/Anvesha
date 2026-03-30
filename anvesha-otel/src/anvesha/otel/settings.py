from __future__ import annotations

import logging
import os
import urllib.parse
from re import compile
from typing import Dict, Optional

logger = logging.getLogger(__name__)

ENV_OTEL_EXPORTER_OTLP_ENDPOINT = "OTEL_EXPORTER_OTLP_ENDPOINT"
ENV_ANVESHA_COLLECTOR_ENDPOINT = "ANVESHA_COLLECTOR_ENDPOINT"
ENV_ANVESHA_GRPC_PORT = "ANVESHA_GRPC_PORT"
ENV_ANVESHA_PROJECT_NAME = "ANVESHA_PROJECT_NAME"
ENV_ANVESHA_CLIENT_HEADERS = "ANVESHA_CLIENT_HEADERS"
ENV_ANVESHA_API_KEY = "ANVESHA_API_KEY"

DEFAULT_PROJECT_NAME = "default"
GRPC_PORT = 4317


def get_env_collector_endpoint() -> Optional[str]:
    return os.getenv(ENV_ANVESHA_COLLECTOR_ENDPOINT) or os.getenv(ENV_OTEL_EXPORTER_OTLP_ENDPOINT)


def get_env_project_name() -> str:
    return os.getenv(ENV_ANVESHA_PROJECT_NAME, DEFAULT_PROJECT_NAME)


def get_env_client_headers() -> Optional[Dict[str, str]]:
    if headers_str := os.getenv(ENV_ANVESHA_CLIENT_HEADERS):
        return parse_env_headers(headers_str)
    return None


def get_env_anvesha_auth_header(api_key: str | None = None) -> Optional[Dict[str, str]]:
    token = api_key or os.getenv(ENV_ANVESHA_API_KEY)
    if token:
        return {"authorization": f"Bearer {token}"}
    return None


def get_env_grpc_port() -> int:
    if not (port := os.getenv(ENV_ANVESHA_GRPC_PORT)):
        return GRPC_PORT
    if port.isnumeric():
        return int(port)
    raise ValueError(f"Invalid value for {ENV_ANVESHA_GRPC_PORT}: {port}")


_OWS = r"[ \t]*"
_KEY_FORMAT = r"[\x21\x23-\x27\x2a\x2b\x2d\x2e\x30-\x39\x41-\x5a\x5e-\x7a\x7c\x7e]+"
_VALUE_FORMAT = r"[\x21\x23-\x2b\x2d-\x3a\x3c-\x5b\x5d-\x7e]*"
_KEY_VALUE_FORMAT = rf"{_OWS}{_KEY_FORMAT}{_OWS}={_OWS}{_VALUE_FORMAT}{_OWS}"

_HEADER_PATTERN = compile(_KEY_VALUE_FORMAT)
_DELIMITER_PATTERN = compile(r"[ \t]*,[ \t]*")


def parse_env_headers(value: str) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for header in _DELIMITER_PATTERN.split(value):
        if not header:
            continue
        match = _HEADER_PATTERN.fullmatch(header.strip())
        if not match:
            parts = header.split("=", 1)
            if len(parts) != 2:
                continue
            name, raw_value = parts
            encoded = f"{urllib.parse.quote(name)}={urllib.parse.quote(raw_value)}"
            match = _HEADER_PATTERN.fullmatch(encoded.strip())
            if not match:
                logger.warning("Ignoring invalid header from %s", ENV_ANVESHA_CLIENT_HEADERS)
                continue
        name, raw_value = header.split("=", 1)
        headers[urllib.parse.unquote(name).strip().lower()] = urllib.parse.unquote(raw_value).strip()
    return headers
