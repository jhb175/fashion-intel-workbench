"""Source model."""

import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from app.models._compat import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Source(Base):
    """Sources table."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    monitor_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID,
        ForeignKey("monitor_groups.id"),
        nullable=True,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    collect_interval_minutes: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )
    last_collected_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_collect_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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
    monitor_group = relationship("MonitorGroup", back_populates="sources")
    articles = relationship("Article", back_populates="source", lazy="selectin")
