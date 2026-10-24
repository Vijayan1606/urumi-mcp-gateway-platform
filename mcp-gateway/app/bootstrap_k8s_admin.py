import os

from sqlalchemy import select

from app.auth_service import create_user
from app.db import SessionLocal
from app.models import APIKey, User
from app.security import get_key_prefix, hash_api_key


def bootstrap_admin():
    email = os.getenv(
        "GATEWAY_BOOTSTRAP_ADMIN_EMAIL", ""
    ).strip().lower()

    raw_key = os.getenv(
        "GATEWAY_BOOTSTRAP_ADMIN_KEY", ""
    ).strip()

    # Bootstrap is optional during local development.
    if not email and not raw_key:
        return

    if not email or "@" not in email:
        raise RuntimeError("Invalid bootstrap administrator email.")

    if not raw_key.startswith("urumi_"):
        raise RuntimeError("Invalid bootstrap administrator API key.")

    db = SessionLocal()

    try:
        existing = db.scalar(
            select(User).where(User.email == email)
        )

        if existing:
            print(
                "Bootstrap skipped: administrator already exists.",
                flush=True,
            )
            return

        admin = create_user(
            db=db,
            email=email,
            role="admin",
        )

        record = APIKey(
            user_id=admin.id,
            name="Kubernetes Bootstrap Admin",
            key_prefix=get_key_prefix(raw_key),
            key_hash=hash_api_key(raw_key),
            is_active=True,
        )

        db.add(record)
        db.commit()

        print("Administrator bootstrap completed.", flush=True)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_admin()
