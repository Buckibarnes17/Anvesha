Anvesha extraction from Phoenix

Copied for tracing-only implementation:
- phoenix-otel package
- OTLP decode + trace schemas + attribute helpers
- project/time/json helpers
- DB models + engine + span insertion + bulk inserter
- OTLP HTTP/gRPC ingest routers
- project/span/trace REST routers
- root pyproject.toml as packaging reference only

Not copied:
- datasets, experiments, evaluators, prompts, playground, auth, full UI, GraphQL stack

Important:
- packages/phoenix-otel is the cleanest SDK slice
- src/phoenix/db/models.py is much larger than needed; trim to Project/Trace/Span/ProjectSession for Anvesha
- pyproject.toml is included only as a dependency/reference source

Additional broad support copied:
- full db package
- full trace package
- full utilities package
- full server/api package
- core server support modules (config, auth, telemetry, main/app entrypoints)
