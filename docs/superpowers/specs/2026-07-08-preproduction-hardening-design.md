# Pre-production hardening (P0 + P1) — Design

**Date:** 2026-07-08
**Branch:** feat/food-suggestions-and-quick-wins
**Status:** Approved, in implementation

## Goal

Make the working NutriScan MVP safe to run as a real service by clearing the P0 and
most of the P1 items in `TODO.md`. CI (GitHub Actions) is **deferred** — documented in
`TODO.md` only, not implemented.

## Guiding constraints

- **Preserve the core invariant:** AI never originates a health-critical number; deterministic
  engines do. None of this work moves math into a prompt.
- **No behavior change in dev.** Defaults keep the current zero-setup dev flow working.
  Hardening (fail-fast, migrations, JSON logs) engages only under `APP_ENV=prod`.
- **Incremental, verified delivery:** implement item-by-item, verify each before moving on.

## New configuration surface

Added to `app/config.py` (pydantic-settings) and `.env.example`, all with safe defaults:

| Var | Default | Purpose |
|-----|---------|---------|
| `APP_ENV` | `dev` | `dev` \| `prod` — gates fail-fast checks & migration expectations |
| `RATE_LIMIT_ENABLED` | `true` | Master switch; `false` removes limiting entirely |
| `RATE_LIMIT_AI_PER_MINUTE` | `10` | Per-identity per-minute cap on AI endpoints |
| `RATE_LIMIT_AI_PER_DAY` | `200` | Per-identity per-day cap (protects free-tier key) |
| `LOG_LEVEL` | `INFO` | Root log level |
| `LOG_JSON` | `false` | `true` → structured JSON logs (prod) |

## Items

### 1. Automated tests (pytest) — built first, the foundation
- `backend/requirements-dev.txt`: `pytest`, `pytest-cov`.
- `tests/conftest.py`: temp-file SQLite via `DATABASE_URL` env override; `TestClient` used as a
  context manager so `lifespan`/`init_db` runs; `client`, `auth_client` (registered+logged-in),
  and `fake_gemini` fixtures. `fake_gemini` monkeypatches `gemini.analyze_images`,
  `ask_question`, `target_guidance`, `suggest_foods` → **no real API calls**.
- Modules: `test_nutrition.py`, `test_scoring.py`, `test_consumption_engine.py`, `test_auth.py`,
  `test_profile.py`, `test_consumption_api.py`, `test_lookup.py` (monkeypatched `httpx`),
  `test_rate_limit.py`, `test_config.py`.
- Run: `pytest`; single: `pytest tests/test_scoring.py::test_name`.

### 2. Config & secret hardening
- `Settings.validate_for_env()`: when `APP_ENV=prod`, hard-fail (raise on startup) on default
  `JWT_SECRET`, missing `GEMINI_API_KEY`, or wildcard (`*`) CORS. In `dev`, warn only.
- Called from `lifespan` before serving.

### 3. Rate limiting (custom, in-memory)
- `app/services/ratelimit.py`: fixed-window counters keyed by identity (user id if authed, else
  client IP). Tracks per-minute + per-day windows. `now` injectable for deterministic tests.
- `deps.rate_limit_ai` dependency on the 4 AI routes (`/analyze`, `/ask`, `/profile/guidance`,
  `/consumption/suggestions`). Over limit → **429** + `Retry-After`.
- `RATE_LIMIT_ENABLED=false` → dependency is a no-op.
- Per-process only; multi-instance → Redis noted as future work in TODO.

### 4. Dockerfile + docker-compose
- `backend/Dockerfile` (python:3.12-slim, non-root, uvicorn), `.dockerignore`.
- `frontend/Dockerfile` (node build → nginx serving `dist/`, proxying `/api` + `/health`),
  `nginx.conf`, `.dockerignore`.
- `docker-compose.yml`: backend + frontend + **optional Postgres** (commented profile; SQLite
  default). Passes env through.

### 5. DB migrations (Alembic) — coexistence strategy
- Add `alembic/` with `env.py` wired to `Base.metadata` + `settings.database_url`; one initial
  migration matching current schema (`users`, `profiles`, `consumption_logs`).
- **Dev keeps `init_db()` create_all** (zero setup). **Prod runs `alembic upgrade head`.**
  This avoids breaking the current dev experience while giving prod real migrations.

### 6. Structured logging + request IDs
- `app/logging_config.py`: stdlib logging, plain or JSON (`LOG_JSON`), level from `LOG_LEVEL`.
- Request-ID middleware: read/generate `X-Request-ID`, bind to log records, echo in response.
- `gemini._generate` logs failovers (model, attempt, status).

### 7. Global error handling
- Exception handlers in `main.py`: `AIServiceError` → its status; `RequestValidationError` →
  clean 422; unhandled → 500 with generic message + request id, **no stack trace leaked**, full
  detail logged server-side.

### CI — deferred (documented only)
Replace the CI TODO line with a description of what it will do: on every push/PR, install backend
deps + run `pytest`, and run `tsc` / `vite build` on the frontend, as the merge gate.

## Testing strategy

Each item ships with tests (item 1 builds the harness). Verify after every item via `pytest`
plus, where relevant, the existing end-to-end smoke flow. No item is "done" until its tests pass.

## Out of scope

CI implementation, Sentry/error-tracking (P2), response caching (P2), Redis-backed rate limiting,
per-user timezones, product/AI feature ideas.
