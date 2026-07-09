"""Application configuration loaded from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_JWT_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # dev | prod. In prod, insecure config (default secret, missing key, wildcard CORS) is fatal
    # at startup rather than a silent warning.
    app_env: str = "dev"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # Fallback models tried in order when the primary is overloaded / rate-limited.
    gemini_fallback_models: str = "gemini-2.5-flash,gemini-2.0-flash"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Day boundary for consumption tracking. IANA timezone name (e.g. "America/New_York");
    # falls back to UTC if the name is unknown. Determines when "today" rolls over.
    app_timezone: str = "UTC"

    # Logging. log_json=true emits structured JSON lines (good for prod log aggregation).
    log_level: str = "INFO"
    log_json: bool = False

    # Rate limiting for the AI endpoints (protects the free-tier key). Set
    # rate_limit_enabled=false to remove the limit entirely. Per identity = user id if
    # authenticated, else client IP. In-memory / per process (see services/ratelimit.py).
    rate_limit_enabled: bool = True
    rate_limit_ai_per_minute: int = 10
    rate_limit_ai_per_day: int = 200

    # Persistence (SQLite by default; swap the URL for Postgres in production).
    database_url: str = "sqlite:///./nutriscan.db"

    # Auth / JWT. Override jwt_secret in production!
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    @property
    def is_prod(self) -> bool:
        return self.app_env.strip().lower() == "prod"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_for_env(self) -> list[str]:
        """Return a list of configuration problems. The caller treats these as fatal in prod
        and as warnings in dev (see main.lifespan)."""
        problems: list[str] = []
        if self.jwt_secret == DEFAULT_JWT_SECRET:
            problems.append("JWT_SECRET is still the insecure default — set a strong random value.")
        if not self.gemini_api_key:
            problems.append("GEMINI_API_KEY is not set — AI endpoints (/analyze, /ask, …) will fail.")
        if "*" in self.cors_origin_list:
            problems.append("CORS_ORIGINS contains '*' — lock it to your real frontend origin(s).")
        return problems

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
