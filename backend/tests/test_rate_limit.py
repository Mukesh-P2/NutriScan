"""Rate limiter: the fixed-window engine, and enforcement + disable switch on an AI endpoint."""

import pytest

from app.config import settings
from app.schemas import AskResponse
from app.services.ratelimit import RateLimiter, limiter

# ---- engine unit tests (deterministic via injected `now`) ----


def test_allows_up_to_the_minute_limit():
    rl = RateLimiter()
    for _ in range(3):
        assert rl.check("id", per_minute=3, per_day=100, now=1000) is None


def test_blocks_over_the_minute_limit():
    rl = RateLimiter()
    for _ in range(3):
        rl.check("id", 3, 100, now=1000)
    assert rl.check("id", 3, 100, now=1000) is not None  # 4th in the same minute


def test_minute_window_resets_next_minute():
    rl = RateLimiter()
    for _ in range(3):
        rl.check("id", 3, 100, now=1000)
    assert rl.check("id", 3, 100, now=1000) is not None
    assert rl.check("id", 3, 100, now=1070) is None  # ~1 minute later


def test_per_day_limit_across_minutes():
    rl = RateLimiter()
    for i in range(5):
        assert rl.check("id", per_minute=100, per_day=5, now=1000 + i * 60) is None
    assert rl.check("id", 100, 5, now=1000 + 5 * 60) is not None


def test_identities_are_isolated():
    rl = RateLimiter()
    rl.check("a", 1, 10, now=1000)
    assert rl.check("a", 1, 10, now=1000) is not None
    assert rl.check("b", 1, 10, now=1000) is None  # different identity unaffected


# ---- endpoint enforcement ----


@pytest.fixture
def reset_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_ai_endpoint_enforces_limit(client, patch_gemini, monkeypatch, reset_limiter):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_ai_per_minute", 2)
    patch_gemini("ask_question", AskResponse(answer="ok"))

    codes = [client.post("/api/ask", data={"question": "q"}).status_code for _ in range(3)]
    assert codes.count(200) == 2
    assert codes[-1] == 429


def test_ai_endpoint_unlimited_when_disabled(client, patch_gemini, reset_limiter):
    # conftest sets RATE_LIMIT_ENABLED=false, so nothing should be throttled.
    patch_gemini("ask_question", AskResponse(answer="ok"))
    codes = [client.post("/api/ask", data={"question": "q"}).status_code for _ in range(15)]
    assert all(c == 200 for c in codes)
