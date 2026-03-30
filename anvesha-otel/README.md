# Anvesha OTEL

This package provides `anvesha.otel.register()` for wiring a tracer provider to the Anvesha collector.

## Quick start

```python
from anvesha.otel import register

tracer_provider = register(
    project_name="repoa-stock-advisor",
    endpoint="http://localhost:8000/v1/traces",
    batch=True,
)
```

## Environment variables

- `ANVESHA_COLLECTOR_ENDPOINT`
- `ANVESHA_PROJECT_NAME`
- `ANVESHA_CLIENT_HEADERS`
- `ANVESHA_API_KEY`
- `ANVESHA_GRPC_PORT`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
