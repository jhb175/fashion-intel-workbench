"""Article tag model."""

import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ArticleTag(Base):
    """Article tags table."""

    __tablename__ = "article_tags"
    __table_args__ = (
        UniqueConstraint("article_id", "tag_type", "tag_value", name="uq_article_tags_article_type_value"),
        Index("idx_article_tags_article_id", "article_id"),
        Index("idx_article_tags_type_value", "tag_type", "tag_value"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("articles.id"), nullable=False
    )
    tag_type: Mapped[str] = mapped_column(String(20), nullable=False)
    tag_value: Mapped[str] = mapped_column(String(200), nullable=False)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    article = relationship("Article", back_populates="tags")
