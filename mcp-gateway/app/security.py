import hashlib
import secrets

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return "urumi_" + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key before storing it."""
    return password_hash.hash(api_key)


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    try:
        return password_hash.verify(api_key, stored_hash)
    except Exception:
        return False


def get_key_prefix(api_key: str) -> str:
    """Return a short prefix for identifying a key in the dashboard."""
    return api_key[:12]
