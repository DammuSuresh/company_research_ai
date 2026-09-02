"""
Application configuration.

All settings are loaded from environment variables (optionally via a .env
file in the backend/ directory). See .env.example for the full list.

Mock mode:
    If GEMINI_API_KEY is not provided, the client automatically falls back to
    deterministic mock data so the app runs out of the box with zero setup.
    This is intentional per the assignment brief ("you may use hardcoded/
    mock responses" when API keys aren't available) -- the real integration
    code paths (LLM call, search call, prompt construction) are still fully
    implemented and used whenever keys are present.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Gemini (LLM) ---
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"

    # --- App ---
    database_url: str = "sqlite:///./data/reports.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:8000"

    @property
    def llm_mock_mode(self) -> bool:
        return not self.gemini_api_key

    @property
    def search_mock_mode(self) -> bool:
        return self.llm_mock_mode

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
