from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlparse

from openinference.semconv.resource import ResourceAttributes
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as _GRPCSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as _HTTPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider as _TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor as _BatchSpanProcessor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor as _SimpleSpanProcessor

from .settings import (
    get_env_anvesha_auth_header,
    get_env_client_headers,
    get_env_collector_endpoint,
    get_env_grpc_port,
    get_env_project_name,
)

PROJECT_NAME = ResourceAttributes.PROJECT_NAME
HTTP_DEFAULT_ENDPOINT = "http://localhost:8000/v1/traces"

TracerProvider = _TracerProvider
SimpleSpanProcessor = _SimpleSpanProcessor
BatchSpanProcessor = _BatchSpanProcessor
HTTPSpanExporter = _HTTPSpanExporter
GRPCSpanExporter = _GRPCSpanExporter


class OTLPTransportProtocol(str, Enum):
    HTTP_PROTOBUF = "http/protobuf"
    GRPC = "grpc"
    INFER = "infer"


def register(
    *,
    endpoint: Optional[str] = None,
    project_name: Optional[str] = None,
    batch: bool = False,
    set_global_tracer_provider: bool = True,
    headers: Optional[Dict[str, str]] = None,
    protocol: Optional[Literal["http/protobuf", "grpc"]] = None,
    verbose: bool = True,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> _TracerProvider:
    project_name = project_name or get_env_project_name()
    tracer_provider_kwargs = dict(kwargs)
    resource = tracer_provider_kwargs.pop("resource", None)
    project_resource = Resource.create({PROJECT_NAME: project_name})
    tracer_provider_kwargs["resource"] = project_resource if resource is None else resource.merge(project_resource)
    tracer_provider = TracerProvider(**tracer_provider_kwargs)

    exporter, resolved_endpoint, resolved_protocol = _build_exporter(
        endpoint=endpoint,
        headers=headers,
        protocol=protocol,
        api_key=api_key,
    )
    processor_cls = BatchSpanProcessor if batch else SimpleSpanProcessor
    tracer_provider.add_span_processor(processor_cls(exporter))

    if set_global_tracer_provider:
        trace_api.set_tracer_provider(tracer_provider)

    if verbose:
        print(_format_details(project_name, resolved_endpoint, resolved_protocol, batch))

    return tracer_provider


def _build_exporter(
    *,
    endpoint: str | None,
    headers: Dict[str, str] | None,
    protocol: str | None,
    api_key: str | None,
) -> tuple[_HTTPSpanExporter | _GRPCSpanExporter, str, OTLPTransportProtocol]:
    merged_headers: Dict[str, str] = {}
    if env_headers := get_env_client_headers():
        merged_headers.update(env_headers)
    if headers:
        merged_headers.update(headers)
    if auth_header := get_env_anvesha_auth_header(api_key):
        merged_headers.update(auth_header)

    raw_endpoint = endpoint or get_env_collector_endpoint() or HTTP_DEFAULT_ENDPOINT
    resolved_protocol = _resolve_protocol(raw_endpoint, protocol)

    if resolved_protocol is OTLPTransportProtocol.GRPC:
        grpc_endpoint = _normalize_grpc_endpoint(raw_endpoint)
        return GRPCSpanExporter(endpoint=grpc_endpoint, headers=merged_headers or None), grpc_endpoint, resolved_protocol

    http_endpoint = _normalize_http_endpoint(raw_endpoint)
    return HTTPSpanExporter(endpoint=http_endpoint, headers=merged_headers or None), http_endpoint, resolved_protocol


def _resolve_protocol(endpoint: str, protocol: str | None) -> OTLPTransportProtocol:
    if protocol:
        return OTLPTransportProtocol(protocol)
    parsed = urlparse(endpoint)
    if parsed.path.endswith("/v1/traces"):
        return OTLPTransportProtocol.HTTP_PROTOBUF
    return OTLPTransportProtocol.HTTP_PROTOBUF


def _normalize_http_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.path.endswith("/v1/traces"):
        return endpoint
    if parsed.path in ("", "/"):
        return endpoint.rstrip("/") + "/v1/traces"
    return endpoint


def _normalize_grpc_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme and parsed.netloc:
        return endpoint
    if endpoint.startswith("localhost") or endpoint.startswith("127.0.0.1"):
        return f"http://{endpoint}"
    return f"http://localhost:{get_env_grpc_port()}"


def _format_details(project_name: str, endpoint: str, protocol: OTLPTransportProtocol, batch: bool) -> str:
    mode = "batch" if batch else "simple"
    return (
        "Anvesha tracing configured\n"
        f"|  project: {project_name}\n"
        f"|  endpoint: {endpoint}\n"
        f"|  protocol: {protocol.value}\n"
        f"|  processor: {mode}\n"
    )
