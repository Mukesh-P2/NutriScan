# NutriScan — TODO & Feature Backlog

Status legend: ✅ done · 🔧 in progress · ⬜ planned

---

## Pre-production essentials  🔧 (active focus — clear these before launch)

Ordered by priority. Goal: make the working MVP safe to run as a real service.

**P0 — must-have**
- [x] **Automated tests** — pytest (52 tests): throwaway in-memory SQLite + TestClient, monkeypatched
      Gemini & Open Food Facts. Covers auth, profile/targets, consumption (log/today/weekly/history/undo),
      suggestions, lookup, analyze, config validation, rate limiting, error handling, and the
      deterministic engines (nutrition, scoring, consumption). Run: `pytest` (see `backend/tests/`).
- [x] **Config & secret hardening** — `APP_ENV` (dev/prod); `Settings.validate_for_env()` fails fast in
      prod on default `JWT_SECRET`, missing `GEMINI_API_KEY`, or wildcard CORS (warns in dev). Enforced
      on startup in `main.lifespan`.
- [x] **Rate limiting** — in-memory fixed-window limiter (`services/ratelimit.py`) per identity
      (user id, else IP) on the AI endpoints (`/analyze`, `/ask`, `/profile/guidance`,
      `/consumption/suggestions`). Configurable via `RATE_LIMIT_ENABLED` / `_AI_PER_MINUTE` / `_AI_PER_DAY`;
      `RATE_LIMIT_ENABLED=false` removes it. 429 + `Retry-After`. *(Per-process — see multi-instance note below.)*
- [x] **Dockerfile + docker-compose** — `backend/Dockerfile` (slim, non-root, uvicorn),
      `frontend/Dockerfile` (Vite build → nginx, proxies `/api`), `docker-compose.yml` (backend +
      frontend + optional Postgres profile). One command: `docker compose up --build`.

**P1 — strongly recommended**
- [x] **DB migrations (Alembic)** — `alembic/` wired to `Base.metadata` + `settings.database_url`;
      initial migration for `users`/`profiles`/`consumption_logs`; `render_as_batch` for SQLite-safe
      ALTERs. **Dev keeps `create_all` on startup; prod runs `alembic upgrade head`.**
- [x] **Structured logging + request IDs** — `logging_config.py` (plain or JSON via `LOG_JSON`, level
      via `LOG_LEVEL`); request-id middleware sets/echoes `X-Request-ID` and binds it to every log line;
      `gemini._generate` logs model failovers.
- [x] **Global error handling** — exception handlers in `main.py`: `AIServiceError` → its status,
      unhandled → clean 500 (`{"detail": ...}`, full detail logged, no stack trace leaked); the
      `{"detail": ...}` shape the frontend relies on is preserved.
- [ ] **CI (GitHub Actions)** — *deferred, not yet implemented.* Planned: a workflow triggered on every
      push and pull request that (1) sets up Python 3.12, installs `backend/requirements-dev.txt`, and runs
      `pytest` from `backend/`; (2) sets up Node, runs `npm ci` and `npm run build` (i.e. `tsc` typecheck +
      `vite build`) in `frontend/`; and (3) is marked a required status check so red builds block merge to
      `main`. Optionally add `alembic upgrade head` against a scratch DB to catch migration drift.

**P2 — nice to have**
- [ ] **Response caching** for identical analyze images / repeated questions.
- [ ] **Error tracking** (e.g. Sentry) + a DB-readiness check on `/health`.
- [ ] **Shared-store rate limiting** (e.g. Redis) — the current limiter is per-process, so it under-counts
      across multiple backend instances. Fine for single-instance; revisit when scaling horizontally.

---

## Recently done
- ✅ Food suggestions (#4), weekly averages, timezone-aware day boundary, lookup caching + auto cross-check
- ✅ Scan history, product compare, share/export, model-chain health badge, status-aware error UX
- ✅ Multi-image product scan → verdict, 0–100 score, pros/cons/tips
- ✅ Daily-needs coverage per nutrient, serving & max-per-day guidance
- ✅ Allergen / veg / diet-tag badges, trans-fat / palm-oil / ultra-processed flags
- ✅ Free-form "Ask" with whole-food fallback + optional image
- ✅ Gemini model failover (retry + fallback chain on 429/5xx)

---

## Roadmap (from README)

### 1. ✅ Login + user profiles
Personalized daily needs instead of the generic "typical adult".
- [x] Introduce persistence (SQLite + SQLAlchemy) — `app/db.py`, `app/models/`
- [x] User model + email/password auth (JWT sessions) — `app/security.py`, `app/routers/auth.py`
- [x] Profile: age, sex, height, weight, activity level, goal (lose/maintain/gain)
- [x] Compute personal targets (Mifflin–St Jeor + RDA-derived) — `app/services/nutrition.py`
- [x] Frontend: login/register pages, auth context, profile form + targets view
- [x] Required-field validation (age/sex/height/weight/activity marked *; generic defaults until complete)
- [x] AI target guidance — `GET /api/profile/guidance`: numbers stay from the formula, Gemini
      advises around the *exact* figures (grounded, no hallucinated numbers) + safety flag & disclaimer
- [x] Wire personalization into scan/ask — optional auth; logged-in users with a complete profile get
      tips + daily-context tailored to their targets/goal (nutrient %DV & score kept on standard refs)

### 2. ✅ Barcode + food-name lookup
Resolve a scanned barcode / product name to real data via Open Food Facts.
- [x] Open Food Facts client (barcode → product, name → search via Search-a-licious)
- [x] Country-aware: optional country filter + explicit region-mismatch & freshness **caveats**
      (data is a hint to verify, never overrides the scanned label — see openfoodfacts.py)
- [x] Endpoints `GET /api/lookup/barcode/{code}` & `/api/lookup/search`; Lookup tab + inline
      "cross-check barcode" on scan results
- [x] Graceful "not found" fallback that points the user back to scanning the label
- [x] Cache lookups (in-memory 1h TTL) to cut latency & API calls — `openfoodfacts.py`
- [x] Auto-cross-check the scanned barcode on scan results (`ScanResponse.barcode_lookup`, best-effort)

### 3. ✅ Consumption tracking  *(needs #1)*
- [x] `serving_nutrition` (numeric per-serving) added to scan output — feeds the tracker
- [x] Log entries (user, product, servings, nutrient totals, day) — `models/consumption.py`
- [x] Deterministic engine — remaining vs. target, per-nutrient effects, overall **achievement %**
      (`services/consumption.py`; no AI guessing of health numbers)
- [x] "Should I eat this?" preview — fills-gaps vs. over-limit advice + general product feedback
- [x] Endpoints: `preview`, `log`, `today`, `history`, delete(undo); **Today** dashboard tab
      (achievement ring, nutrient bars, entries w/ undo, 7-day history) + Consume panel on scans
- [x] Weekly averages — `GET /api/consumption/weekly`, "This week" card on the Today tab
- [x] Consume straight from a Lookup result — `ProductLookupCard` reuses `ConsumePanel` (per-100g → serving)
- [x] Timezone-aware day boundary — `APP_TIMEZONE` setting + `local_today()` used at read & write time

### 4. ✅ Food suggestions  *(needs #3)*
- [x] Recommend foods to fill remaining daily gaps — `GET /api/consumption/suggestions`; gaps computed
      deterministically (targets − intake), AI only picks foods (`services/suggestions.py`, `prompts.py`)
- [x] Factor in local availability + past consumption — optional `country` param + today's eaten foods
      (for variety) are fed into the prompt; `SuggestionsPanel` on the Today tab
- [ ] **Later:** persistent taste/preferences, multi-day history as input, one-tap "log this suggestion"

---

## Additional suggestions

### Quick wins
- [x] **Scan history** (pre-login, via localStorage) — `scanHistory.ts`, "Recent scans" on the Scan tab
- [x] **Compare two products** side by side — `Compare` tab, sourced from scan history, per-nutrient winner
- [x] **Loading / error UX** polish — `ErrorNotice` distinguishes rate-limit (429) vs busy (503) + retry
- [x] **Health `/health` badge** — `HealthBadge` in the header shows the active model chain
- [x] **Share / export** a scan result — Web Share / clipboard + `.txt` download (`shareResult.ts`)

### Backend / quality  *(now tracked under "Pre-production essentials" above)*
- [x] **Automated tests** — pytest for routers + engines with a monkeypatched Gemini client
- [x] **Rate limiting** per IP/user to protect the free-tier key
- [ ] **Response caching** for identical images / repeated questions
- [x] **Structured logging + request IDs** for debugging failovers
- [x] **Dockerfile + docker-compose** for one-command run

### Product / AI
- [ ] **Serving-size slider** — recompute daily-% live for a custom portion
- [ ] **"Healthier alternative" suggestions** for unhealthy verdicts
- [ ] **Multi-language** label OCR + answers
- [ ] **Allergen profile** — flag products against a user's own allergen list (ties into #1)
- [ ] **Meal builder** — combine several scanned items into one meal's totals

### Accessibility / mobile
- [ ] **PWA / installable** app with camera-first capture
- [ ] **Offline queue** — scan now, analyze when back online

---

## Resolved decisions
- Storage: **SQLite + SQLAlchemy** (swap `DATABASE_URL` for Postgres in prod)
- Auth: **email + password + JWT** (7-day tokens)
- Personalized needs: **Mifflin–St Jeor** for calories + RDA-derived macro/limit targets
- Health numbers are **deterministic**; AI only explains/advises around them (never invents figures)
