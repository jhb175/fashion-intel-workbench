"""Brand model."""

import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Brand(Base):
    """Brands table."""

    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    name_zh: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    official_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    social_media_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    naming_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    monitor_group = relationship("MonitorGroup", back_populates="brands")
    logos = relationship(
        "BrandLogo", back_populates="brand", lazy="selectin", cascade="all, delete-orphan"
    )
