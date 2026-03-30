from opentelemetry.sdk.resources import Resource

from .otel import (
    BatchSpanProcessor,
    GRPCSpanExporter,
    HTTPSpanExporter,
    PROJECT_NAME,
    SimpleSpanProcessor,
    TracerProvider,
    register,
)

try:
    from importlib.metadata import version

    __version__ = version("anvesha-otel")
except Exception:
    __version__ = "unknown"

__all__ = [
    "TracerProvider",
    "SimpleSpanProcessor",
    "BatchSpanProcessor",
    "HTTPSpanExporter",
    "GRPCSpanExporter",
    "Resource",
    "PROJECT_NAME",
    "register",
    "__version__",
]
