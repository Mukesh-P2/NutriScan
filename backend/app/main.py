"""FastAPI entrypoint for NutriScan."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analyze, ask

app = FastAPI(title="NutriScan API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(ask.router)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "gemini_configured": bool(settings.gemini_api_key)}
