# NutriScan — TODO & Feature Backlog

Status legend: ✅ done · 🔧 in progress · ⬜ planned

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

### Backend / quality
- [ ] **Automated tests** — pytest for routers + a mocked Gemini client (none exist yet)
- [ ] **Rate limiting** per IP/user to protect the free-tier key
- [ ] **Response caching** for identical images / repeated questions
- [ ] **Structured logging + request IDs** for debugging failovers
- [ ] **Dockerfile + docker-compose** for one-command run

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
