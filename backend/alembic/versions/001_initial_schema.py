"""Initial schema — all tables for Fashion Intel Workbench.

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- monitor_groups ---
    op.create_table(
        "monitor_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column(
            "monitor_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monitor_groups.id"),
            nullable=True,
        ),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("collect_interval_minutes", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_collect_status", sa.String(20), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- articles ---
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sources.id"),
            nullable=False,
        ),
        sa.Column("original_title", sa.String(500), nullable=False),
        sa.Column("original_url", sa.String(1000), unique=True, nullable=False),
        sa.Column("original_language", sa.String(10), nullable=False),
        sa.Column("original_excerpt", sa.Text(), nullable=True),
        sa.Column("chinese_summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("title_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_articles_published_at", "articles", [sa.text("published_at DESC")])
    op.create_index("idx_articles_source_id", "articles", ["source_id"])
    op.create_index("idx_articles_processing_status", "articles", ["processing_status"])
    op.create_index("idx_articles_title_hash", "articles", ["title_hash"])

    # Full-text search index (GIN) on chinese_summary and original_title
    op.execute(
        """
        CREATE INDEX idx_articles_fts
        ON articles
        USING gin (
            (
                to_tsvector('simple', coalesce(chinese_summary, ''))
                || to_tsvector('english', coalesce(original_title, ''))
            )
        )
        """
    )

    # pg_trgm GIN index for fuzzy text search on chinese_summary and original_title
    op.execute(
        """
        CREATE INDEX idx_articles_trgm_summary
        ON articles
        USING gin (chinese_summary gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_articles_trgm_title
        ON articles
        USING gin (original_title gin_trgm_ops)
        """
    )

    # --- article_tags ---
    op.create_table(
        "article_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id"),
            nullable=False,
        ),
        sa.Column("tag_type", sa.String(20), nullable=False),
        sa.Column("tag_value", sa.String(200), nullable=False),
        sa.Column("is_auto", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("article_id", "tag_type", "tag_value", name="uq_article_tags_article_type_value"),
    )
    op.create_index("idx_article_tags_article_id", "article_tags", ["article_id"])
    op.create_index("idx_article_tags_type_value", "article_tags", ["tag_type", "tag_value"])

    # --- brands ---
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name_zh", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("official_name", sa.String(200), nullable=True),
        sa.Column("social_media_name", sa.String(200), nullable=True),
        sa.Column("naming_notes", sa.Text(), nullable=True),
        sa.Column(
            "monitor_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monitor_groups.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- brand_logos ---
    op.create_table(
        "brand_logos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(300), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_format", sa.String(10), nullable=False),
        sa.Column("logo_type", sa.String(50), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("thumbnail_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_brand_logos_brand_id", "brand_logos", ["brand_id"])

    # --- keywords ---
    op.create_table(
        "keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("word_zh", sa.String(200), nullable=False),
        sa.Column("word_en", sa.String(200), nullable=False),
        sa.Column(
            "monitor_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monitor_groups.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- bookmarks ---
    op.create_table(
        "bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "article_id", name="uq_bookmarks_user_article"),
    )

    # --- topic_candidates ---
    op.create_table(
        "topic_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "article_id", name="uq_topic_candidates_user_article"),
    )

    # --- deep_analyses ---
    op.create_table(
        "deep_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("importance", sa.Text(), nullable=False),
        sa.Column("industry_background", sa.Text(), nullable=False),
        sa.Column("follow_up_suggestions", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- daily_briefings ---
    op.create_table(
        "daily_briefings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("briefing_date", sa.Date(), unique=True, nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("has_new_articles", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- briefing_articles ---
    op.create_table(
        "briefing_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "briefing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("daily_briefings.id"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id"),
            nullable=False,
        ),
    )

    # --- knowledge_entries ---
    op.create_table(
        "knowledge_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- knowledge_entry_brands ---
    op.create_table(
        "knowledge_entry_brands",
        sa.Column(
            "knowledge_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_entries.id"),
            primary_key=True,
        ),
        sa.Column("brand_name", sa.String(200), primary_key=True, nullable=False),
    )

    # --- knowledge_entry_keywords ---
    op.create_table(
        "knowledge_entry_keywords",
        sa.Column(
            "knowledge_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_entries.id"),
            primary_key=True,
        ),
        sa.Column("keyword", sa.String(200), primary_key=True, nullable=False),
    )

    # --- ai_providers ---
    op.create_table(
        "ai_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("api_base_url", sa.String(500), nullable=False),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("is_preset", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_status", sa.String(20), nullable=True),
        sa.Column("last_test_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ai_providers")
    op.drop_table("knowledge_entry_keywords")
    op.drop_table("knowledge_entry_brands")
    op.drop_table("knowledge_entries")
    op.drop_table("briefing_articles")
    op.drop_table("daily_briefings")
    op.drop_table("deep_analyses")
    op.drop_table("topic_candidates")
    op.drop_table("bookmarks")
    op.drop_table("keywords")
    op.drop_table("brand_logos")
    op.drop_table("brands")
    op.drop_table("article_tags")
    op.execute("DROP INDEX IF EXISTS idx_articles_trgm_title")
    op.execute("DROP INDEX IF EXISTS idx_articles_trgm_summary")
    op.execute("DROP INDEX IF EXISTS idx_articles_fts")
    op.drop_table("articles")
    op.drop_table("sources")
    op.drop_table("monitor_groups")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
