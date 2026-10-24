from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth_service import authenticate_api_key
from app.db import SessionLocal
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="A valid API key is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = authenticate_api_key(db, credentials.credentials)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired, or revoked API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required.",
        )

    return user
