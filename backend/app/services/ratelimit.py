"""In-memory fixed-window rate limiter.

Deliberately dependency-free and per-process — it mirrors the app's existing in-memory OFF
cache. Good enough to protect the free-tier Gemini key on a single instance; for multiple
instances a shared store (e.g. Redis) would be needed (noted in TODO.md).

`check()` takes an injectable `now` so windows are deterministic in tests.
"""

import time
from dataclasses import dataclass


@dataclass
class _Counter:
    minute_bucket: int = -1
    minute_count: int = 0
    day_bucket: int = -1
    day_count: int = 0


class RateLimiter:
    """Two fixed windows per identity: requests-per-minute and requests-per-day."""

    def __init__(self) -> None:
        self._counters: dict[str, _Counter] = {}

    def check(self, identity: str, per_minute: int, per_day: int, now: float | None = None) -> float | None:
        """Record a request for `identity`. Return None if allowed, else the number of seconds
        to wait before retrying (suitable for a `Retry-After` header)."""
        now = time.time() if now is None else now
        minute_bucket = int(now // 60)
        day_bucket = int(now // 86400)

        c = self._counters.get(identity)
        if c is None:
            c = _Counter()
            self._counters[identity] = c

        if c.minute_bucket != minute_bucket:
            c.minute_bucket, c.minute_count = minute_bucket, 0
        if c.day_bucket != day_bucket:
            c.day_bucket, c.day_count = day_bucket, 0

        if c.minute_count >= per_minute:
            return max(1.0, 60 - (now % 60))
        if c.day_count >= per_day:
            return max(1.0, 86400 - (now % 86400))

        c.minute_count += 1
        c.day_count += 1
        return None

    def reset(self) -> None:
        """Clear all counters (used between tests)."""
        self._counters.clear()


# Module-level singleton shared across requests.
limiter = RateLimiter()
