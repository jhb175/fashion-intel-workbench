"""Monitor group model."""

import uuid

from sqlalchemy import DateTime, Integer, String, Text
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class MonitorGroup(Base):
    """Monitor groups table."""

    __tablename__ = "monitor_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
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
    sources = relationship("Source", back_populates="monitor_group", lazy="selectin")
    brands = relationship("Brand", back_populates="monitor_group", lazy="selectin")
    keywords = relationship("Keyword", back_populates="monitor_group", lazy="selectin")
