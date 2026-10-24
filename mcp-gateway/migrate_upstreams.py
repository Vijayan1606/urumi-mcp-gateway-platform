import json

from app.db import Base, SessionLocal, engine
from app.models import UpstreamServer

# Ensure all registered SQLAlchemy models have their tables.
Base.metadata.create_all(bind=engine)

# Preserve the existing upstream configuration.
UPSTREAMS = {
    "woocommerce": {
        "url": "http://woo-mcp.urumi.svc.cluster.local:8000/mcp",
        "enabled": True,
    },
    "inventory": {
        "url": "http://inventory-mcp.urumi.svc.cluster.local:8000/",
        "enabled": True,
    },
    "customer_support": {
        "url": "http://customer-support-mcp.urumi.svc.cluster.local:8000/",
        "enabled": True,
    },
}


def migrate():
    db = SessionLocal()

    try:
        for name, config in UPSTREAMS.items():
            existing = (
                db.query(UpstreamServer)
                .filter(UpstreamServer.name == name)
                .first()
            )

            if existing:
                print(f"Already exists: {name}")
                continue

            server = UpstreamServer(
                name=name,
                url=config["url"],
                enabled=config["enabled"],
                headers_json=None,
            )

            db.add(server)
            print(f"Prepared: {name}")

        db.commit()
        print("\nMigration completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    migrate()
