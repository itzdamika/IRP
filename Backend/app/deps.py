from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .core.security import decode_token
from .db.models import User
from .db.session import get_db

bearer = HTTPBearer(auto_error=False)


def user_from_token(db: Session, token: str) -> User | None:
    """Resolve user from raw JWT string (WebSockets, PDF ?token=, etc.)."""
    t = (token or "").strip()
    if not t:
        return None
    try:
        payload = decode_token(t)
        sub = payload.get("sub")
        if not sub:
            return None
    except Exception:
        return None
    return db.get(User, sub)


def get_current_user(
    db: Session = Depends(get_db),
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if not cred or cred.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(cred.credentials)
        sub = payload.get("sub")
        if not sub:
            raise ValueError("no sub")
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.get(User, sub)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def get_optional_user(
    db: Session = Depends(get_db),
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User | None:
    if not cred:
        return None
    try:
        return get_current_user(db, cred)
    except HTTPException:
        return None
