"""Knowledge entry models."""

import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from app.models._compat import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeEntry(Base):
    """Knowledge entries table."""

    __tablename__ = "knowledge_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    brands = relationship(
        "KnowledgeEntryBrand",
        back_populates="knowledge_entry",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    keywords = relationship(
        "KnowledgeEntryKeyword",
        back_populates="knowledge_entry",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class KnowledgeEntryBrand(Base):
    """Knowledge entry brands association table."""

    __tablename__ = "knowledge_entry_brands"

    knowledge_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("knowledge_entries.id"),
        primary_key=True,
    )
    brand_name: Mapped[str] = mapped_column(
        String(200), primary_key=True, nullable=False
    )

    # Relationships
    knowledge_entry = relationship("KnowledgeEntry", back_populates="brands")


class KnowledgeEntryKeyword(Base):
    """Knowledge entry keywords association table."""

    __tablename__ = "knowledge_entry_keywords"

    knowledge_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("knowledge_entries.id"),
        primary_key=True,
    )
    keyword: Mapped[str] = mapped_column(
        String(200), primary_key=True, nullable=False
    )

    # Relationships
    knowledge_entry = relationship("KnowledgeEntry", back_populates="keywords")
