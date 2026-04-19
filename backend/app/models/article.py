"""Article model."""

import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Article(Base):
    """Articles table."""

    __tablename__ = "articles"
    __table_args__ = (
        Index("idx_articles_published_at", "published_at"),
        Index("idx_articles_source_id", "source_id"),
        Index("idx_articles_processing_status", "processing_status"),
        Index("idx_articles_title_hash", "title_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("sources.id"), nullable=False
    )
    original_title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_url: Mapped[str] = mapped_column(
        String(1000), unique=True, nullable=False, index=True
    )
    original_language: Mapped[str] = mapped_column(String(10), nullable=False)
    original_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    chinese_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    collected_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processing_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    title_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
    source = relationship("Source", back_populates="articles")
    tags = relationship(
        "ArticleTag", back_populates="article", lazy="selectin", cascade="all, delete-orphan"
    )
    bookmarks = relationship(
        "Bookmark", back_populates="article", lazy="selectin", cascade="all, delete-orphan"
    )
    topic_candidates = relationship(
        "TopicCandidate", back_populates="article", lazy="selectin", cascade="all, delete-orphan"
    )
    deep_analysis = relationship(
        "DeepAnalysis", back_populates="article", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    briefing_articles = relationship(
        "BriefingArticle", back_populates="article", lazy="selectin"
    )
