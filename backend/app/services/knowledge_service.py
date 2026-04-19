"""Knowledge entry service — CRUD, search by category/keyword, association matching."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import (
    KnowledgeEntry,
    KnowledgeEntryBrand,
    KnowledgeEntryKeyword,
)
from app.schemas.knowledge import (
    KnowledgeEntryCreateRequest,
    KnowledgeEntryListResponse,
    KnowledgeEntryResponse,
    KnowledgeEntryUpdateRequest,
)
from app.utils.errors import NotFoundError, ValidationError


class KnowledgeService:
    """Handles knowledge entry CRUD, search, and association matching."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # List entries (paginated, with optional category & keyword filters)
    # ------------------------------------------------------------------

    async def list_entries(
        self,
        category: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> KnowledgeEntryListResponse:
        """Return a paginated list of knowledge entries with optional filters."""
        base = select(KnowledgeEntry)

        if category is not None:
            base = base.where(KnowledgeEntry.category == category)

        if keyword is not None:
            # Search in title, summary, associated brands, and associated keywords
            brand_subq = (
                select(KnowledgeEntryBrand.knowledge_entry_id)
                .where(KnowledgeEntryBrand.brand_name.ilike(f"%{keyword}%"))
            )
            kw_subq = (
                select(KnowledgeEntryKeyword.knowledge_entry_id)
                .where(KnowledgeEntryKeyword.keyword.ilike(f"%{keyword}%"))
            )
            base = base.where(
                or_(
                    KnowledgeEntry.title.ilike(f"%{keyword}%"),
                    KnowledgeEntry.summary.ilike(f"%{keyword}%"),
                    KnowledgeEntry.id.in_(brand_subq),
                    KnowledgeEntry.id.in_(kw_subq),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        items_stmt = (
            base.order_by(KnowledgeEntry.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(items_stmt)
        entries = list(result.scalars().all())

        items = [self._to_response(entry) for entry in entries]
        return KnowledgeEntryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # Get single entry
    # ------------------------------------------------------------------

    async def get_entry(self, entry_id: uuid.UUID) -> KnowledgeEntryResponse:
        """Return a single knowledge entry by ID."""
        entry = await self._get_entry_or_raise(entry_id)
        return self._to_response(entry)

    # ------------------------------------------------------------------
    # Create entry
    # ------------------------------------------------------------------

    async def create_entry(
        self, body: KnowledgeEntryCreateRequest
    ) -> KnowledgeEntryResponse:
        """Create a new knowledge entry with brand and keyword associations."""
        entry = KnowledgeEntry(
            title=body.title,
            category=body.category.value,
            content=body.content,
            summary=body.summary,
        )
        self.db.add(entry)
        await self.db.flush()

        # Add brand associations
        for brand_name in body.brands:
            self.db.add(
                KnowledgeEntryBrand(
                    knowledge_entry_id=entry.id,
                    brand_name=brand_name,
                )
            )

        # Add keyword associations
        for kw in body.keywords:
            self.db.add(
                KnowledgeEntryKeyword(
                    knowledge_entry_id=entry.id,
                    keyword=kw,
                )
            )

        await self.db.flush()
        await self.db.refresh(entry)
        return self._to_response(entry)

    # ------------------------------------------------------------------
    # Update entry
    # ------------------------------------------------------------------

    async def update_entry(
        self, entry_id: uuid.UUID, body: KnowledgeEntryUpdateRequest
    ) -> KnowledgeEntryResponse:
        """Update an existing knowledge entry. Replace brands/keywords if provided."""
        entry = await self._get_entry_or_raise(entry_id)

        # Update scalar fields
        if body.title is not None:
            entry.title = body.title
        if body.category is not None:
            entry.category = body.category.value
        if body.content is not None:
            entry.content = body.content
        if body.summary is not None:
            entry.summary = body.summary

        # Replace brand associations if provided
        if body.brands is not None:
            await self.db.execute(
                delete(KnowledgeEntryBrand).where(
                    KnowledgeEntryBrand.knowledge_entry_id == entry_id
                )
            )
            for brand_name in body.brands:
                self.db.add(
                    KnowledgeEntryBrand(
                        knowledge_entry_id=entry_id,
                        brand_name=brand_name,
                    )
                )

        # Replace keyword associations if provided
        if body.keywords is not None:
            await self.db.execute(
                delete(KnowledgeEntryKeyword).where(
                    KnowledgeEntryKeyword.knowledge_entry_id == entry_id
                )
            )
            for kw in body.keywords:
                self.db.add(
                    KnowledgeEntryKeyword(
                        knowledge_entry_id=entry_id,
                        keyword=kw,
                    )
                )

        await self.db.flush()
        await self.db.refresh(entry)
        return self._to_response(entry)

    # ------------------------------------------------------------------
    # Delete entry
    # ------------------------------------------------------------------

    async def delete_entry(self, entry_id: uuid.UUID) -> None:
        """Delete a knowledge entry and cascade associations."""
        entry = await self._get_entry_or_raise(entry_id)
        await self.db.delete(entry)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Match entries by article tags (brands + keywords)
    # ------------------------------------------------------------------

    async def match_entries_for_article(
        self,
        brands: list[str],
        keywords: list[str],
    ) -> list[KnowledgeEntryResponse]:
        """Find knowledge entries that match any of the given brands or keywords."""
        if not brands and not keywords:
            return []

        conditions = []
        if brands:
            brand_subq = (
                select(KnowledgeEntryBrand.knowledge_entry_id).where(
                    KnowledgeEntryBrand.brand_name.in_(brands)
                )
            )
            conditions.append(KnowledgeEntry.id.in_(brand_subq))

        if keywords:
            kw_subq = (
                select(KnowledgeEntryKeyword.knowledge_entry_id).where(
                    KnowledgeEntryKeyword.keyword.in_(keywords)
                )
            )
            conditions.append(KnowledgeEntry.id.in_(kw_subq))

        stmt = select(KnowledgeEntry).where(or_(*conditions)).distinct()
        result = await self.db.execute(stmt)
        entries = list(result.scalars().all())
        return [self._to_response(e) for e in entries]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_entry_or_raise(self, entry_id: uuid.UUID) -> KnowledgeEntry:
        """Load a knowledge entry or raise NotFoundError."""
        stmt = select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError("知识条目不存在")
        return entry

    @staticmethod
    def _to_response(entry: KnowledgeEntry) -> KnowledgeEntryResponse:
        """Convert a KnowledgeEntry ORM object to a response model."""
        return KnowledgeEntryResponse(
            id=entry.id,
            title=entry.title,
            category=entry.category,
            content=entry.content,
            summary=entry.summary,
            brands=[b.brand_name for b in entry.brands],
            keywords=[k.keyword for k in entry.keywords],
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
