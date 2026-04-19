"""Keyword model."""

import uuid

from sqlalchemy import DateTime, ForeignKey, String
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Keyword(Base):
    """Keywords table."""

    __tablename__ = "keywords"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    word_zh: Mapped[str] = mapped_column(String(200), nullable=False)
    word_en: Mapped[str] = mapped_column(String(200), nullable=False)
    monitor_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("monitor_groups.id"),
        nullable=True,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    monitor_group = relationship("MonitorGroup", back_populates="keywords")
