"""Shared FastAPI dependencies: the current authenticated user.

``get_current_user`` is reused by every protected route (profile now; consumption
tracking and suggestions later).
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.security import decode_token
from app.services.ratelimit import limiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
# auto_error=False so anonymous requests are allowed (returns None instead of 401).
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_CRED_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    subject = decode_token(token)
    if subject is None or not subject.isdigit():
        raise _CRED_EXC
    user = db.get(User, int(subject))
    if user is None:
        raise _CRED_EXC
    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)
) -> User | None:
    """Like get_current_user but returns None for anonymous requests instead of raising.

    Used by scan/ask so they work logged-out (generic defaults) and personalize when logged in.
    """
    if not token:
        return None
    subject = decode_token(token)
    if subject is None or not subject.isdigit():
        return None
    return db.get(User, int(subject))


def rate_limit_ai(
    request: Request, user: User | None = Depends(get_current_user_optional)
) -> None:
    """Rate-limit the AI endpoints per identity (user id if signed in, else client IP).

    A no-op when RATE_LIMIT_ENABLED is false. Over the limit → 429 with a Retry-After header.
    """
    if not settings.rate_limit_enabled:
        return
    identity = (
        f"user:{user.id}" if user is not None
        else f"ip:{request.client.host if request.client else 'unknown'}"
    )
    retry_after = limiter.check(
        identity, settings.rate_limit_ai_per_minute, settings.rate_limit_ai_per_day
    )
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit reached for AI requests. Please wait and try again.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
