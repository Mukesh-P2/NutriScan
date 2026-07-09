"""FastAPI entrypoint for NutriScan."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import init_db
from app.logging_config import configure_logging, request_id_var
from app.routers import analyze, ask, auth, consumption, lookup, profile
from app.services.gemini import AIServiceError

logger = logging.getLogger("nutriscan")


def _check_config() -> None:
    """Fail fast in prod on insecure config; warn (but continue) in dev."""
    problems = settings.validate_for_env()
    if not problems:
        return
    detail = "Configuration issues detected:\n  - " + "\n  - ".join(problems)
    if settings.is_prod:
        raise RuntimeError(detail + "\nRefusing to start with insecure configuration (APP_ENV=prod).")
    logger.warning("%s\n(APP_ENV=dev, continuing anyway.)", detail)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    _check_config()
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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Assign/propagate an X-Request-ID and bind it to every log line for this request."""
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.request_id = rid
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


@app.exception_handler(AIServiceError)
async def ai_service_error_handler(request: Request, exc: AIServiceError):
    """Safety net: turn any uncaught AI failure into its intended HTTP status (429/503/502)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)},
        headers={"X-Request-ID": _request_id(request)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Consistent JSON for unexpected errors — full detail is logged, never sent to the client."""
    rid = _request_id(request)
    logger.exception("Unhandled error [%s] on %s %s", rid, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal error occurred."},
        headers={"X-Request-ID": rid},
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
