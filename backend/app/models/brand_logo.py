"""Brand logo model."""

import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class BrandLogo(Base):
    """Brand logos table."""

    __tablename__ = "brand_logos"
    __table_args__ = (
        Index("idx_brand_logos_brand_id", "brand_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("brands.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(300), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    logo_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    brand = relationship("Brand", back_populates="logos")
