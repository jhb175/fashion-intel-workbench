"""Bookmark and topic candidate models."""

import uuid

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Bookmark(Base):
    """Bookmarks table."""

    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_bookmarks_user_article"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("articles.id"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article", back_populates="bookmarks")


class TopicCandidate(Base):
    """Topic candidates table."""

    __tablename__ = "topic_candidates"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "article_id", name="uq_topic_candidates_user_article"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("articles.id"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="topic_candidates")
    article = relationship("Article", back_populates="topic_candidates")
