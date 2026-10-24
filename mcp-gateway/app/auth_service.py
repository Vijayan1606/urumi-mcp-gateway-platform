from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import APIKey, User
from app.security import (
    generate_api_key,
    get_key_prefix,
    hash_api_key,
    verify_api_key,
)


def create_user(
    db: Session,
    email: str,
    role: str = "member",
) -> User:
    """Create a user with a validated role."""

    email = email.strip().lower()

    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")

    if role not in {"admin", "member"}:
        raise ValueError("Role must be 'admin' or 'member'.")

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise ValueError("A user with this email already exists.")

    user = User(email=email, role=role)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def issue_api_key(
    db: Session,
    user_id: int,
    name: str,
) -> tuple[APIKey, str]:
    """Create a key and return its record plus the plaintext key once."""

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise ValueError("User not found or inactive.")

    if not name.strip():
        raise ValueError("API key name is required.")

    raw_key = generate_api_key()

    record = APIKey(
        user_id=user.id,
        name=name.strip(),
        key_prefix=get_key_prefix(raw_key),
        key_hash=hash_api_key(raw_key),
        is_active=True,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record, raw_key


def authenticate_api_key(
    db: Session,
    raw_key: str,
) -> User | None:
    """Return the user associated with a valid, active API key."""

    if not raw_key:
        return None

    prefix = get_key_prefix(raw_key)

    records = db.scalars(
        select(APIKey).where(
            APIKey.key_prefix == prefix,
            APIKey.is_active.is_(True),
        )
    ).all()

    for record in records:
        user = db.get(User, record.user_id)

        if (
            user is not None
            and user.is_active
            and verify_api_key(raw_key, record.key_hash)
        ):
            return user

    return None


def revoke_api_key(
    db: Session,
    key_id: int,
    requesting_user: User,
) -> bool:
    """Revoke an API key owned by the caller or an admin."""

    record = db.get(APIKey, key_id)

    if record is None or not record.is_active:
        return False

    if (
        requesting_user.role != "admin"
        and record.user_id != requesting_user.id
    ):
        raise PermissionError(
            "You can only revoke your own API keys."
        )

    record.is_active = False
    record.revoked_at = datetime.now(timezone.utc)

    db.commit()

    return True
