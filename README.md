# NutriScan 🥗

A web app that analyzes food products from photos and answers food questions using AI (Google Gemini).

## Features (v1)

- **Scan a product** — upload or capture **multiple images** of a food label (front, ingredients, nutrition table). Gemini merges them and returns:
  - Healthy / moderate / unhealthy verdict + a 0–100 score
  - Pros, cons, and actionable tips
  - **Daily-needs coverage** — % of an adult's recommended daily intake each nutrient provides
  - Recommended serving size and max-per-day guidance
  - Barcode & product name (captured now; DB lookup planned)
  - `missing_info` hints so you know when to add another photo
- **Ask** — free-form food questions ("What does an apple contain?"), with a graceful whole-food fallback and optional image attachment.

## Tech stack

- **Backend:** FastAPI + `google-genai`, structured (JSON-schema) output validated by Pydantic
- **Frontend:** React + Vite + TypeScript + Tailwind CSS

## Prerequisites

- Python 3.12+
- Node 18+
- A Google Gemini API key — get one free at https://aistudio.google.com/apikey

## Setup & run

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

## Project structure

```
fitness/
├── backend/
│   └── app/
│       ├── main.py            # FastAPI app + CORS + /health
│       ├── config.py          # env / API key
│       ├── schemas.py         # Pydantic models (= Gemini output schema)
│       ├── prompts.py         # system + task prompts
│       ├── routers/           # /api/analyze, /api/ask
│       └── services/gemini.py # all Gemini calls
└── frontend/
    └── src/
        ├── App.tsx            # Scan / Ask tabs
        ├── api.ts, types.ts
        ├── pages/             # Scan, Ask
        └── components/        # ImagePicker, AnalysisCard, NutrientList
```

## Roadmap (later)

- Login + user profiles (personalized daily needs)
- Barcode + food-name lookup via a food database (e.g. Open Food Facts)
- Consumption tracking: who ate what, intake averages, consumed vs. remaining
- Food suggestions based on local availability and past consumption
```
