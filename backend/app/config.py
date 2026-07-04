"""Application settings, sourced from environment variables / .env file."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor to backend/.env so the settings load regardless of the working
# directory (uvicorn, pytest, or the MCP server launched from elsewhere).
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Google Gemini API key for the explanation layer. Optional: without it
    # the deterministic fallback explainer is used and scans still work.
    gemini_api_key: str = ""

    # Primary Gemini model. Free-tier quotas differ per model; if the primary
    # is exhausted or unavailable the fallbacks below are tried in order.
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_fallback_models: str = ("gemini-2.5-flash-lite,"
                                   "gemini-2.5-flash,gemini-2.0-flash")

    @property
    def gemini_model_chain(self) -> list[str]:
        chain = [self.gemini_model]
        for m in self.gemini_fallback_models.split(","):
            m = m.strip()
            if m and m not in chain:
                chain.append(m)
        return chain

    # MongoDB Atlas connection string. Optional: without it an in-memory
    # mongomock instance is used (fine for local dev, data not persisted).
    mongo_uri: str = ""
    mongo_db_name: str = "scamshield"

    # JWT signing. Override in production!
    jwt_secret: str = "dev-only-secret-change-me-in-production-0000"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 72

    # Comma-separated list of allowed CORS origins.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
