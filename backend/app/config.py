"""Application configuration via pydantic-settings.

All values are read from environment variables (case-insensitive).
A .env file in the project root is loaded automatically when present.
"""

from __future__ import annotations

import json
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    # asyncpg driver — used by the async SQLAlchemy engine at runtime
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/workflow_map"
    )
    # psycopg2 driver — used by Alembic (sync) migrations only
    DATABASE_SYNC_URL: str = (
        "postgresql+psycopg2://postgres:password@localhost:5432/workflow_map"
    )

    # ── JWT Auth ──────────────────────────────────────────────────────────────
    # Generate with: openssl rand -hex 32
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # ── Notion ────────────────────────────────────────────────────────────────
    NOTION_TOKEN: str = ""

    # ── Teams notification (SMTP relay via Teams channel email) ───────────────
    TEAMS_NOTIFICATION_EMAIL: str = "fc748c69.joycity.com@kr.teams.ms"
    SMTP_HOST: str = "smtp.office365.com"
    SMTP_PORT: int = 587
    SMTP_FROM_EMAIL: str = "workflow-map@joycity.com"

    # ── Anthropic ─────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""

    # ── Git ───────────────────────────────────────────────────────────────────
    GIT_REMOTE_URL: str = "https://github.com/joycityDSBI/workflow-map"
    GIT_REPO_LOCAL_PATH: str = "/app/git-workspace"

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Comma-separated fallback
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v  # type: ignore[return-value]


settings = Settings()
