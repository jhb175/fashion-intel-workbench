"""Database type compatibility layer.

Provides JSONB and UUID types that work with both PostgreSQL and SQLite.
"""

import uuid as _uuid

from sqlalchemy import JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID

from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")


# JSONB → JSON on SQLite
JSONB = JSON if _is_sqlite else PG_JSONB


class UUID(TypeDecorator):
    """UUID type that works on both PostgreSQL (native UUID) and SQLite (CHAR(36))."""

    impl = String(36) if _is_sqlite else PG_UUID(as_uuid=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if _is_sqlite:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if _is_sqlite and isinstance(value, str):
            return _uuid.UUID(value)
        return value
