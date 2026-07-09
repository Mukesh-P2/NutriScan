"""Shared pytest fixtures.

Every test runs against a throwaway in-memory SQLite database (never the real one) and,
for AI-backed routes, a monkeypatched Gemini so no real API calls are made.
"""

import os

# Deterministic test environment — MUST be set before importing app (settings is a
# singleton built at import time from the environment).
os.environ["JWT_SECRET"] = "test-secret-not-default"
os.environ["GEMINI_API_KEY"] = ""
os.environ["APP_ENV"] = "dev"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["APP_TIMEZONE"] = "UTC"
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 - registers ORM models on Base.metadata
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def engine():
    """A fresh in-memory database per test (StaticPool shares the one connection across threads)."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(eng)
        eng.dispose()


@pytest.fixture
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _client(engine, raise_server_exceptions=True):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


@pytest.fixture
def client(engine):
    """TestClient wired to the throwaway engine via a get_db override."""
    with _client(engine) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_raise(engine):
    """Like `client` but returns 500 responses instead of re-raising, so the global error
    handler can be exercised."""
    with _client(engine, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """A client already registered and carrying a bearer token."""
    r = client.post(
        "/api/auth/register",
        json={"email": "user@test.com", "password": "password123", "name": "U"},
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def patch_gemini(monkeypatch):
    """Replace a gemini.* function with one that returns a fixed value (no API call)."""
    from app.services import gemini

    def _patch(func_name: str, return_value):
        monkeypatch.setattr(gemini, func_name, lambda *args, **kwargs: return_value)

    return _patch
