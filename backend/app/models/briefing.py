"""Daily briefing and briefing article models."""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey
from app.models._compat import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class DailyBriefing(Base):
    """Daily briefings table."""

    __tablename__ = "daily_briefings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    briefing_date: Mapped[date] = mapped_column(
        Date, unique=True, nullable=False
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    has_new_articles: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    briefing_articles = relationship(
        "BriefingArticle",
        back_populates="briefing",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class BriefingArticle(Base):
    """Briefing articles table - links briefings to articles."""

    __tablename__ = "briefing_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    briefing_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("daily_briefings.id"), nullable=False
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("articles.id"), nullable=False
    )

    # Relationships
    briefing = relationship("DailyBriefing", back_populates="briefing_articles")
    article = relationship("Article", back_populates="briefing_articles")
