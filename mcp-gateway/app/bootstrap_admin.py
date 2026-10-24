import getpass

from app.auth_service import create_user, issue_api_key
from app.db import SessionLocal
from app.models import User


def main():
    email = input("Administrator email: ").strip().lower()

    if not email or "@" not in email:
        print("Please enter a valid email address.")
        return

    db = SessionLocal()

    try:
        existing = db.query(User).filter_by(email=email).first()

        if existing:
            print("This account already exists.")
            print("No new administrator or API key was created.")
            return

        admin = create_user(
            db=db,
            email=email,
            role="admin",
        )

        key_name = input("API key name [Local Admin]: ").strip()
        key_name = key_name or "Local Admin"

        key_record, raw_key = issue_api_key(
            db=db,
            user_id=admin.id,
            name=key_name,
        )

        print("\nAdministrator created successfully.")
        print(f"User ID: {admin.id}")
        print(f"API key ID: {key_record.id}")
        print(f"API key: {raw_key}")
        print("\nIMPORTANT: Copy this key now.")
        print("It will not be displayed again.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
