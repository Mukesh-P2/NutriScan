"""FastAPI entrypoint for NutriScan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import analyze, ask, auth, consumption, lookup, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables on startup (no-op if they already exist)
    yield


app = FastAPI(title="NutriScan API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(ask.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(lookup.router)
app.include_router(consumption.router)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "gemini_configured": bool(settings.gemini_api_key),
        "model_chain": settings.model_chain,
    }
