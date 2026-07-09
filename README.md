# NutriScan 🥗

A web app that analyzes food products from photos, answers food questions, and tracks what you eat against personalized daily targets — using AI (Google Gemini) for reading labels and giving advice.

> **Design principle:** AI reads labels and writes advice, but it **never invents health-critical numbers**. All targets, scores, intake math, and recommendations are computed by validated formulas / deterministic rules. The AI is always handed the exact numbers and asked only to explain them.

## Features

- **Scan a product** — upload or capture **multiple images** of a food label (front, ingredients, nutrition table). Gemini merges them and returns:
  - Healthy / moderate / unhealthy verdict + a 0–100 score (the score is **recomputed deterministically** from the read nutrients, so it's stable)
  - Pros, cons, and actionable tips
  - **Daily-needs coverage** — % of recommended daily intake each nutrient provides
  - Allergen / veg / diet-tag badges + trans-fat / palm-oil / ultra-processed flags
  - Recommended serving size, max-per-day, and whole-pack impact (if you give the pack weight)
  - `missing_info` hints so you know when to add another photo
- **Ask** — free-form food questions ("What does an apple contain?"), with a graceful whole-food fallback and optional image attachment.
- **Accounts & profiles** — register / log in (JWT); set age, sex, height, weight, activity level, and goal to get **personalized daily nutrition targets** (calories via Mifflin–St Jeor + RDA-derived macros) instead of the generic adult baseline. AI *guidance* is grounded in those exact numbers (it never invents figures). When signed in, Scan/Ask tips are tailored to your targets.
- **Food-database lookup** — search Open Food Facts by name or barcode (or cross-check a scanned barcode). Country-aware, with explicit caveats: the same barcode can differ by region or change over time, so results are a hint to verify against the physical label — never a silent override.
- **Consumption tracking** — tap “I ate this” on a scan (or a database lookup) to log it against your daily targets. Before logging, a deterministic **“should I eat this?”** check tells you whether it fills what you still need or pushes you over a limit, plus general feedback on the product. A **Today** dashboard shows an overall achievement %, per-nutrient progress (consumed / remaining / over), logged items (with undo), a 7-day history, and **weekly averages**. All the intake math is rule-based — the AI never guesses the numbers.
- **Food suggestions** — “What should I eat next?” recommends specific foods to fill what's *left* of today. The remaining gaps are computed deterministically (targets − intake); the AI only picks foods, factoring in an optional country (local availability) and the foods you've already eaten (variety). The day boundary is timezone-aware (`APP_TIMEZONE`).
- **Scan history, compare & share** — recent scans are saved on your device (works logged-out); open any two in the **Compare** tab to line up scores and nutrients side by side, or share/export a result (native share, clipboard, or `.txt`). A header badge shows the active AI model chain.

## Tech stack

- **Backend:** FastAPI + `google-genai` (structured JSON-schema output validated by Pydantic), SQLAlchemy + SQLite, JWT auth, `httpx`
- **Frontend:** React + Vite + TypeScript + Tailwind CSS
- **Resilience:** Gemini calls fail over across a configurable model chain on rate-limit / overload (429 / 5xx)

## Prerequisites

- Python 3.12+
- Node 18+
- A Google Gemini API key — get one free at https://aistudio.google.com/apikey

## Setup & run

### 0. Clone the repo

```bash
git clone https://github.com/Mukesh-P2/NutriScan.git
cd NutriScan
```

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                 # then edit .env and set GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Backend runs at http://localhost:8000 (docs at `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173 and proxies `/api` to the backend.

### 3. Run the tests (backend)

```bash
cd backend
pip install -r requirements-dev.txt
pytest                                   # whole suite
pytest tests/test_scoring.py::test_junk_food_scores_unhealthy   # a single test
```

Tests use a throwaway in-memory SQLite DB and a monkeypatched Gemini / Open Food Facts, so
they need **no API key and hit no network**.

### 4. Run everything with Docker (optional)

```bash
docker compose up --build
#   frontend → http://localhost:8080   backend → http://localhost:8000
```

Set `JWT_SECRET`, `GEMINI_API_KEY`, and `APP_ENV=prod` in a `.env` next to `docker-compose.yml`
before any real deployment. A Postgres profile is available: `docker compose --profile postgres up`.

### Database migrations

Dev creates tables automatically on startup (`create_all`). For production, use Alembic:

```bash
cd backend
alembic upgrade head        # apply migrations (Postgres or SQLite)
alembic revision --autogenerate -m "describe change"   # after changing models/
```

## Using the app — feature walkthrough

NutriScan is organised into tabs across the top. Most features work logged-out; **tracking and personalization need an account**.

### 🔍 Scan  *(the main feature)*
1. On the **Scan** tab, add one or more photos of a food label — front, ingredients list, nutrition table (multiple angles are merged into one analysis).
2. *(Optional)* Enter the **total pack weight** (e.g. `90g`) to also get whole-pack impact and how much to eat.
3. Click **Analyze** → verdict (healthy / moderate / unhealthy), a 0–100 score, pros / cons / tips, per-nutrient daily-needs coverage, allergen / veg / diet badges, and processing flags.
4. If a barcode is visible it's **auto cross-checked** against Open Food Facts and shown as a hint below (your scanned label stays the source of truth).
5. Use **🔗 Share / copy** or **⬇ Download .txt** to export the result.
6. Every scan is saved under **Recent scans** (on this device) — click one to reopen it, or ✕ to remove.

### 💬 Ask
Type any food question ("Is oat milk healthy?", "What's in an apple?") and optionally attach a photo. Whole foods get a natural-food explanation.

### 🗄️ Lookup
Search **Open Food Facts** by product **name** or **barcode**; add a country to bias to your region. Results lead with caveats (region / freshness) — always verify against the physical label. When logged in, use **Eat this?** on a result to log it to today (database values are per 100 g; set servings to your portion, e.g. `1.5` = 150 g).

### ⚖️ Compare
Pick any **two of your past scans** to see scores and per-serving nutrients side by side — the healthier value in each row is highlighted (more protein / fiber, less sugar / saturated fat / sodium).

### 👤 Log in & Profile
Register or log in (top-right tab). On **Profile**, fill age, sex, height, weight, activity level and goal to unlock **personalized daily targets** (calories via Mifflin–St Jeor + RDA macros) and **AI guidance** grounded in those exact numbers. Signed-in users also get Scan / Ask tips tailored to their targets.

### 📊 Today  *(tracking + suggestions — needs login + a complete profile)*
- **Log food:** on any Scan or Lookup result open **Eat this?**, set servings, optionally **Check today's fit** ("should I eat this?"), then **✓ I ate this**.
- The dashboard shows your **achievement ring**, per-nutrient **progress bars** (consumed / remaining / over), **logged items** (with Undo), a **7-day history**, and **This week's averages**.
- **What should I eat next?** suggests specific foods to fill what's *left* of today (optionally by country). The remaining gaps are computed exactly; the AI only picks the foods.

### Header badge
The pill next to the logo shows the active AI model chain (green = ready, amber = key missing, grey = backend down). Hover for the full failover chain.

## API endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/api/analyze` | optional | Scan image(s) → analysis + auto barcode cross-check (personalized when logged in) |
| `POST` | `/api/ask` | optional | Free-form food question |
| `POST` | `/api/auth/register`, `/api/auth/login` | — | Create account / log in (JWT) |
| `GET`  | `/api/auth/me` | ✓ | Current user |
| `GET`/`PUT` | `/api/profile` | ✓ | Read / update profile |
| `GET`  | `/api/profile/targets` | ✓ | Personalized daily targets (Mifflin–St Jeor + RDA) |
| `GET`  | `/api/profile/guidance` | ✓ | AI guidance grounded in those exact targets |
| `GET`  | `/api/lookup/barcode/{code}`, `/api/lookup/search` | — | Open Food Facts lookup (country-aware, caveat-first) |
| `POST` | `/api/consumption/preview` | ✓ | "Should I eat this?" vs. what's left of the day |
| `POST` | `/api/consumption/log` | ✓ | Record an item, return updated day |
| `GET`  | `/api/consumption/today` | ✓ | Today's progress + entries |
| `GET`  | `/api/consumption/history` | ✓ | Per-day achievement (last N days) |
| `GET`  | `/api/consumption/weekly` | ✓ | Weekly averages — avg intake + achievement |
| `GET`  | `/api/consumption/suggestions` | ✓ | AI foods to fill today's remaining gaps |
| `DELETE` | `/api/consumption/{id}` | ✓ | Undo an entry |
| `GET`  | `/health` | — | Status + active Gemini model chain |

## Project structure

```
fitness/
├── backend/
│   └── app/
│       ├── main.py             # FastAPI app + CORS + lifespan (DB init) + /health
│       ├── config.py           # env / API key / DB / JWT / model-failover / timezone settings
│       ├── db.py               # SQLAlchemy engine, session, Base (shared)
│       ├── security.py         # password hashing (bcrypt) + JWT
│       ├── deps.py             # get_current_user / get_current_user_optional
│       ├── models/             # ORM: user.py (User, Profile), consumption.py (ConsumptionLog)
│       ├── schemas.py          # Gemini output schemas (analysis, ask, guidance, serving nutrition)
│       ├── auth_schemas.py     # auth / profile / targets DTOs
│       ├── lookup_schemas.py   # Open Food Facts DTOs
│       ├── consumption_schemas.py
│       ├── prompts.py          # system + task prompts
│       ├── routers/            # analyze, ask, auth, profile, lookup, consumption (+ weekly, suggestions)
│       └── services/           # gemini.py (AI + failover), nutrition.py (targets), openfoodfacts.py
│                               #   (lookup + cache), consumption.py (intake engine), suggestions.py
└── frontend/
    └── src/
        ├── App.tsx             # Scan / Ask / Lookup / Compare / Today / Profile tabs
        ├── AuthContext.tsx     # global auth state
        ├── api.ts, auth.ts, consumption.ts, types.ts
        ├── scanHistory.ts, shareResult.ts, offNutrition.ts   # localStorage history, share, OFF→serving
        ├── pages/              # Scan, Ask, Lookup, Compare, Today, Login, Profile
        └── components/         # ImagePicker, AnalysisCard, NutrientList, ProductLookupCard,
                                #   ConsumePanel, SuggestionsPanel, HealthBadge, ErrorNotice
```

## Production readiness

NutriScan is a **working MVP with the pre-production essentials in place**. What's already done:

**Done**
- **Config fail-fast** — set `APP_ENV=prod` and the app refuses to start with an insecure config
  (default `JWT_SECRET`, missing `GEMINI_API_KEY`, or wildcard CORS). In dev these only warn.
- **Rate limiting** on the AI endpoints per identity (user id, else IP) — tune via
  `RATE_LIMIT_ENABLED` / `RATE_LIMIT_AI_PER_MINUTE` / `RATE_LIMIT_AI_PER_DAY`.
- **Automated tests** — a pytest suite (52 tests) covering the engines, routers, config, rate
  limiting, and error handling; no key or network needed.
- **Migrations** — Alembic for prod (`alembic upgrade head`); dev still auto-creates tables.
- **Structured logging + request IDs** (`X-Request-ID` on every response; `LOG_JSON=true` for prod)
  and **global error handling** (unexpected errors → clean 500, no stack-trace leakage).
- **Docker** — `docker compose up --build` runs backend + nginx-served frontend (+ optional Postgres).
- **CI** — `.github/workflows/ci.yml` runs the backend `pytest` suite (Python 3.12), a scratch-DB
  `alembic upgrade head` (migration-drift check), and the frontend build (`npm ci` + `npm run build`)
  on every push to `main` and every PR. It activates once the repo is pushed to GitHub; mark the jobs
  as required status checks to block merges on red.

**Still to do before a large public launch**
- Swap SQLite for **Postgres** (`DATABASE_URL`) — the compose Postgres profile needs a driver
  (`psycopg[binary]`) added to `requirements.txt`.
- Rate limiting and the Open Food Facts cache are **in-memory per process**; use a shared store
  (e.g. Redis) across multiple instances. The day boundary is **app-global** (`APP_TIMEZONE`), not per user.
- **Error tracking** (e.g. Sentry) and **response caching** for repeat images / questions — see `TODO.md`.
- Serve over **HTTPS** and lock `CORS_ORIGINS` to your real frontend origin.

**Product caveat**
- AI label OCR can misread; scores and targets stay deterministic, but users should always verify against the physical label (the UI says so).

**Verdict:** ready for pilots and small deployments; complete the "still to do" list for a large public launch.

## Roadmap

See `TODO.md` for the full backlog.

- ✅ Login + user profiles (personalized daily needs), wired into scan/ask
- ✅ AI target guidance grounded in the computed numbers
- ✅ Barcode + food-name lookup via Open Food Facts (country-aware, caveat-first)
- ✅ Consumption tracking: log intake, consumed vs. remaining, daily achievement % + history + weekly averages
- ✅ Food suggestions based on remaining daily gaps, local availability (country) & recent foods
- ✅ Quick wins: scan history, product compare, share/export, model-chain health badge, status-aware errors
