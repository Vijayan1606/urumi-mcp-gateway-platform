from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="member",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    api_keys = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
    )

    key_prefix: Mapped[str] = mapped_column(
        String(16),
        index=True,
    )

    key_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="api_keys",
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    server: Mapped[str] = mapped_column(
        String(100),
    )

    tool: Mapped[str] = mapped_column(
        String(150),
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )

    duration_ms: Mapped[float] = mapped_column(
        Float,
    )

    outcome: Mapped[str] = mapped_column(
        String(30),
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

class UpstreamServer(Base):
    __tablename__ = "upstream_servers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    url: Mapped[str] = mapped_column(
        String(500),
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    # Optional server-side HTTP headers, such as Authorization.
    # Never return this field through the API.
    headers_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
