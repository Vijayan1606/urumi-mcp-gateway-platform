from app.db import SessionLocal
from app.models import UpstreamServer


def get_upstreams() -> dict:
    """Return upstream configurations stored in the database."""
    db = SessionLocal()

    try:
        servers = db.query(UpstreamServer).all()

        return {
            server.name: {
                "url": server.url,
                "enabled": server.enabled,
                "headers": server.headers_json,
            }
            for server in servers
        }
    finally:
        db.close()


def get_upstream(name: str) -> dict | None:
    """Return one upstream configuration, or None if it doesn't exist."""
    db = SessionLocal()

    try:
        server = (
            db.query(UpstreamServer)
            .filter(UpstreamServer.name == name)
            .first()
        )

        if server is None:
            return None

        return {
            "url": server.url,
            "enabled": server.enabled,
            "headers": server.headers_json,
        }
    finally:
        db.close()
