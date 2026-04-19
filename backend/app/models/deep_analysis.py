"""Deep analysis model."""

import uuid

from sqlalchemy import DateTime, ForeignKey, Text
from app.models._compat import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class DeepAnalysis(Base):
    """Deep analyses table."""

    __tablename__ = "deep_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("articles.id"), unique=True, nullable=False
    )
    importance: Mapped[str] = mapped_column(Text, nullable=False)
    industry_background: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_suggestions: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    article = relationship("Article", back_populates="deep_analysis")
