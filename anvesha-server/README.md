# Anvesha Server

This is a small tracing-first backend scaffold for Anvesha.

It keeps only the pieces needed to support Yuktha tracing:
- OTLP HTTP trace ingest at `/v1/traces`
- SQLite storage for `projects`, `project_sessions`, `traces`, and `spans`
- REST read APIs for projects, traces, and spans

## Quick start

```powershell
cd D:\IITM-Pravartak\Anvesha\Anvesha\anvesha-server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
anvesha-server
```

By default the server starts at `http://localhost:8000` and creates `anvesha.db` in the project directory.
