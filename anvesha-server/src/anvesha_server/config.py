from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_PROJECT_NAME = "default"


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    database_url: str
    log_level: str
    default_project_name: str
    sql_echo: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        host=os.getenv("ANVESHA_HOST", "0.0.0.0"),
        port=int(os.getenv("ANVESHA_PORT", "8000")),
        database_url=os.getenv("ANVESHA_DATABASE_URL", "sqlite+aiosqlite:///./anvesha.db"),
        log_level=os.getenv("ANVESHA_LOG_LEVEL", "info"),
        default_project_name=os.getenv("ANVESHA_DEFAULT_PROJECT_NAME", DEFAULT_PROJECT_NAME),
        sql_echo=_get_bool("ANVESHA_SQL_ECHO"),
    )
