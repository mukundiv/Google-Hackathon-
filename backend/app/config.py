"""Runtime configuration.

Every external data source is independently switchable between a `mock`
implementation (rich, deterministic, zero credentials) and a `live` one.
Mock is the default everywhere so the console is fully functional before any
API integration work happens.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = BACKEND_ROOT / "app" / "data" / "seed"

GeminiMode = Literal["mock", "live"]
YouTubeMode = Literal["mock", "live"]
TrendsMode = Literal["mock", "bigquery"]
AnalyticsMode = Literal["mock", "oauth"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_ROOT.parent / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- provider modes -------------------------------------------------
    gemini_mode: GeminiMode = "mock"
    youtube_mode: YouTubeMode = "mock"
    trends_mode: TrendsMode = "mock"
    analytics_mode: AnalyticsMode = "mock"

    # --- credentials (never required in mock mode) ----------------------
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_grounded_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    youtube_api_key: str | None = None
    gcp_project_id: str | None = None
    google_oauth_client_secrets: str | None = None

    # --- behaviour ------------------------------------------------------
    database_url: str = f"sqlite:///{BACKEND_ROOT / 'coe.db'}"
    cache_ttl_seconds: int = 60 * 60 * 6
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def effective_gemini_mode(self) -> GeminiMode:
        """Live mode silently degrades to mock when no key is present."""
        if self.gemini_mode == "live" and not self.gemini_api_key:
            return "mock"
        return self.gemini_mode

    def effective_youtube_mode(self) -> YouTubeMode:
        if self.youtube_mode == "live" and not self.youtube_api_key:
            return "mock"
        return self.youtube_mode

    def effective_trends_mode(self) -> TrendsMode:
        if self.trends_mode == "bigquery" and not self.gcp_project_id:
            return "mock"
        return self.trends_mode

    def effective_analytics_mode(self) -> AnalyticsMode:
        if self.analytics_mode == "oauth" and not self.google_oauth_client_secrets:
            return "mock"
        return self.analytics_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
