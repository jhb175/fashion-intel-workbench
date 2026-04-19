"""Dashboard API router – overview, recent articles, trending tags."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.article import Article
from app.models.bookmark import Bookmark, TopicCandidate
from app.models.monitor_group import MonitorGroup
from app.models.source import Source
from app.models.tag import ArticleTag
from app.models.user import User
from app.responses import success_response
from app.utils.auth import get_current_user

router = APIRouter(tags=["dashboard"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today_start() -> datetime:
    """Return the start of today (00:00 UTC)."""
    return datetime.combine(date.today(), time.min, tzinfo=timezone.utc)


# ===========================================================================
# GET /api/v1/dashboard/overview
# ===========================================================================


@router.get("/api/v1/dashboard/overview")
async def dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get dashboard data overview.

    Returns today_new_articles, group_distribution, pending_count,
    bookmark_count, and topic_candidate_count.
    """
    today_start = _today_start()

    # today_new_articles – articles collected today
    today_count_q = select(func.count(Article.id)).where(
        Article.collected_at >= today_start
    )
    today_new_articles: int = (await db.execute(today_count_q)).scalar_one()

    # group_distribution – monitor_group name → article count
    group_dist_q = (
        select(MonitorGroup.name, func.count(Article.id))
        .join(Source, Source.monitor_group_id == MonitorGroup.id)
        .join(Article, Article.source_id == Source.id)
        .group_by(MonitorGroup.name)
    )
    group_rows = (await db.execute(group_dist_q)).all()
    group_distribution: dict[str, int] = {name: cnt for name, cnt in group_rows}

    # pending_count
    pending_q = select(func.count(Article.id)).where(
        Article.processing_status == "pending"
    )
    pending_count: int = (await db.execute(pending_q)).scalar_one()

    # bookmark_count for current user
    bm_q = select(func.count(Bookmark.id)).where(
        Bookmark.user_id == current_user.id
    )
    bookmark_count: int = (await db.execute(bm_q)).scalar_one()

    # topic_candidate_count for current user
    tc_q = select(func.count(TopicCandidate.id)).where(
        TopicCandidate.user_id == current_user.id
    )
    topic_candidate_count: int = (await db.execute(tc_q)).scalar_one()

    return success_response(data={
        "today_new_articles": today_new_articles,
        "group_distribution": group_distribution,
        "pending_count": pending_count,
        "bookmark_count": bookmark_count,
        "topic_candidate_count": topic_candidate_count,
    })


# ===========================================================================
# GET /api/v1/dashboard/recent-articles
# ===========================================================================


@router.get("/api/v1/dashboard/recent-articles")
async def dashboard_recent_articles(
    limit: int = Query(20, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get recent articles (max 20) ordered by published_at DESC.

    Each article includes tags and bookmark/topic-candidate status for the
    current user.
    """
    articles_q = (
        select(Article)
        .options(selectinload(Article.tags))
        .order_by(Article.published_at.desc().nullslast())
        .limit(limit)
    )
    result = await db.execute(articles_q)
    articles = result.scalars().all()

    # Collect article ids for bookmark / topic-candidate lookup
    article_ids = [a.id for a in articles]

    bookmarked_ids: set = set()
    topic_ids: set = set()
    if article_ids:
        bm_q = select(Bookmark.article_id).where(
            Bookmark.user_id == current_user.id,
            Bookmark.article_id.in_(article_ids),
        )
        bookmarked_ids = set((await db.execute(bm_q)).scalars().all())

        tc_q = select(TopicCandidate.article_id).where(
            TopicCandidate.user_id == current_user.id,
            TopicCandidate.article_id.in_(article_ids),
        )
        topic_ids = set((await db.execute(tc_q)).scalars().all())

    items = []
    for a in articles:
        items.append({
            "id": str(a.id),
            "original_title": a.original_title,
            "chinese_summary": a.chinese_summary,
            "original_url": a.original_url,
            "original_language": a.original_language,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "processing_status": a.processing_status,
            "tags": [
                {"tag_type": t.tag_type, "tag_value": t.tag_value, "is_auto": t.is_auto}
                for t in a.tags
            ],
            "is_bookmarked": a.id in bookmarked_ids,
            "is_topic_candidate": a.id in topic_ids,
        })

    return success_response(data=items)


# ===========================================================================
# GET /api/v1/dashboard/trending-tags
# ===========================================================================


@router.get("/api/v1/dashboard/trending-tags")
async def dashboard_trending_tags(
    days: int = Query(7, ge=1, le=30),
    top_n: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get trending tags per monitor group.

    For each monitor group, return the top tags (by frequency) from articles
    collected in the last *days* days.
    """
    from datetime import timedelta

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Fetch all monitor groups
    groups_result = await db.execute(
        select(MonitorGroup).order_by(MonitorGroup.sort_order)
    )
    groups = groups_result.scalars().all()

    trending: dict[str, list[dict]] = {}
    for group in groups:
        tag_q = (
            select(ArticleTag.tag_value, ArticleTag.tag_type, func.count().label("count"))
            .join(Article, Article.id == ArticleTag.article_id)
            .join(Source, Source.id == Article.source_id)
            .where(
                Source.monitor_group_id == group.id,
                Article.collected_at >= since,
            )
            .group_by(ArticleTag.tag_value, ArticleTag.tag_type)
            .order_by(func.count().desc())
            .limit(top_n)
        )
        rows = (await db.execute(tag_q)).all()
        trending[group.name] = [
            {"tag_value": tag_value, "tag_type": tag_type, "count": count}
            for tag_value, tag_type, count in rows
        ]

    return success_response(data=trending)
