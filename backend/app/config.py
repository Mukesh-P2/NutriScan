"""Application configuration loaded from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # Fallback models tried in order when the primary is overloaded / rate-limited.
    gemini_fallback_models: str = "gemini-2.5-flash,gemini-2.0-flash"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Day boundary for consumption tracking. IANA timezone name (e.g. "America/New_York");
    # falls back to UTC if the name is unknown. Determines when "today" rolls over.
    app_timezone: str = "UTC"

    # Persistence (SQLite by default; swap the URL for Postgres in production).
    database_url: str = "sqlite:///./nutriscan.db"

    # Auth / JWT. Override jwt_secret in production!
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def model_chain(self) -> list[str]:
        """Primary model first, then fallbacks — deduped, order preserved."""
        raw = [self.gemini_model, *self.gemini_fallback_models.split(",")]
        seen: set[str] = set()
        chain: list[str] = []
        for m in (x.strip() for x in raw):
            if m and m not in seen:
                seen.add(m)
                chain.append(m)
        return chain


settings = Settings()
