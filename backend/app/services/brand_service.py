"""Brand service – CRUD, naming search (fuzzy matching), and Logo management."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brand import Brand
from app.models.brand_logo import BrandLogo
from app.utils.errors import NotFoundError


class BrandService:
    """Business logic for brand operations including naming search and logo management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Brand CRUD
    # ------------------------------------------------------------------

    async def list_brands(
        self,
        page: int = 1,
        page_size: int = 20,
        monitor_group_id: uuid.UUID | None = None,
    ) -> dict:
        """Return a paginated list of brands."""
        stmt = select(Brand).options(selectinload(Brand.logos))

        if monitor_group_id is not None:
            stmt = stmt.where(Brand.monitor_group_id == monitor_group_id)

        # Count total
        from sqlalchemy import func

        count_stmt = select(func.count()).select_from(Brand)
        if monitor_group_id is not None:
            count_stmt = count_stmt.where(Brand.monitor_group_id == monitor_group_id)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginate
        stmt = stmt.order_by(Brand.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        brands = list(result.scalars().all())

        return {
            "items": [self._brand_to_dict(b) for b in brands],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_brand(self, data: dict) -> dict:
        """Create a new brand and return its representation."""
        brand = Brand(
            name_zh=data["name_zh"],
            name_en=data["name_en"],
            official_name=data.get("official_name"),
            social_media_name=data.get("social_media_name"),
            naming_notes=data.get("naming_notes"),
            monitor_group_id=data.get("monitor_group_id"),
        )
        self.db.add(brand)
        await self.db.flush()
        await self.db.refresh(brand)
        return self._brand_to_dict(brand)

    async def update_brand(self, brand_id: uuid.UUID, data: dict) -> dict:
        """Update an existing brand."""
        brand = await self._get_brand_or_404(brand_id)
        for field in ("name_zh", "name_en", "official_name", "social_media_name", "naming_notes", "monitor_group_id"):
            if field in data:
                setattr(brand, field, data[field])
        await self.db.flush()
        await self.db.refresh(brand)
        return self._brand_to_dict(brand)

    async def delete_brand(self, brand_id: uuid.UUID) -> None:
        """Delete a brand and its associated logos."""
        brand = await self._get_brand_or_404(brand_id)
        await self.db.delete(brand)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Brand naming search (fuzzy matching)
    # ------------------------------------------------------------------

    async def search_naming(self, query: str) -> list[dict]:
        """Fuzzy search brands by name_zh, name_en, or official_name using ILIKE."""
        if not query or not query.strip():
            return []

        pattern = f"%{query.strip()}%"
        stmt = select(Brand).where(
            or_(
                Brand.name_zh.ilike(pattern),
                Brand.name_en.ilike(pattern),
                Brand.official_name.ilike(pattern),
            )
        ).order_by(Brand.name_en)

        result = await self.db.execute(stmt)
        brands = list(result.scalars().all())
        return [self._brand_naming_to_dict(b) for b in brands]

    # ------------------------------------------------------------------
    # Logo management
    # ------------------------------------------------------------------

    async def list_logos(self, brand_id: uuid.UUID) -> list[dict]:
        """Return all logos for a brand."""
        await self._get_brand_or_404(brand_id)
        stmt = (
            select(BrandLogo)
            .where(BrandLogo.brand_id == brand_id)
            .order_by(BrandLogo.created_at.desc())
        )
        result = await self.db.execute(stmt)
        logos = list(result.scalars().all())
        return [self._logo_to_dict(logo) for logo in logos]

    async def create_logo(self, brand_id: uuid.UUID, data: dict) -> dict:
        """Create a logo record for a brand."""
        await self._get_brand_or_404(brand_id)
        logo = BrandLogo(
            brand_id=brand_id,
            file_name=data["file_name"],
            file_path=data["file_path"],
            file_format=data["file_format"],
            logo_type=data["logo_type"],
            file_size_bytes=data.get("file_size_bytes"),
            thumbnail_path=data.get("thumbnail_path"),
        )
        self.db.add(logo)
        await self.db.flush()
        await self.db.refresh(logo)
        return self._logo_to_dict(logo)

    async def update_logo(
        self, brand_id: uuid.UUID, logo_id: uuid.UUID, data: dict
    ) -> dict:
        """Update logo metadata (logo_type, file_name)."""
        logo = await self._get_logo_or_404(brand_id, logo_id)
        for field in ("logo_type", "file_name"):
            if field in data:
                setattr(logo, field, data[field])
        await self.db.flush()
        await self.db.refresh(logo)
        return self._logo_to_dict(logo)

    async def delete_logo(self, brand_id: uuid.UUID, logo_id: uuid.UUID) -> str:
        """Delete a logo record and return its file_path for cleanup."""
        logo = await self._get_logo_or_404(brand_id, logo_id)
        file_path = logo.file_path
        await self.db.delete(logo)
        await self.db.flush()
        return file_path

    async def get_logo(self, brand_id: uuid.UUID, logo_id: uuid.UUID) -> dict:
        """Get a single logo record."""
        logo = await self._get_logo_or_404(brand_id, logo_id)
        return self._logo_to_dict(logo)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_brand_or_404(self, brand_id: uuid.UUID) -> Brand:
        stmt = select(Brand).where(Brand.id == brand_id)
        result = await self.db.execute(stmt)
        brand = result.scalar_one_or_none()
        if brand is None:
            raise NotFoundError("品牌不存在")
        return brand

    async def _get_logo_or_404(
        self, brand_id: uuid.UUID, logo_id: uuid.UUID
    ) -> BrandLogo:
        stmt = select(BrandLogo).where(
            BrandLogo.id == logo_id,
            BrandLogo.brand_id == brand_id,
        )
        result = await self.db.execute(stmt)
        logo = result.scalar_one_or_none()
        if logo is None:
            raise NotFoundError("Logo 不存在")
        return logo

    @staticmethod
    def _brand_to_dict(brand: Brand) -> dict:
        return {
            "id": str(brand.id),
            "name_zh": brand.name_zh,
            "name_en": brand.name_en,
            "official_name": brand.official_name,
            "social_media_name": brand.social_media_name,
            "naming_notes": brand.naming_notes,
            "monitor_group_id": str(brand.monitor_group_id) if brand.monitor_group_id else None,
            "logo_count": len(brand.logos) if brand.logos else 0,
            "created_at": brand.created_at.isoformat() if brand.created_at else None,
            "updated_at": brand.updated_at.isoformat() if brand.updated_at else None,
        }

    @staticmethod
    def _brand_naming_to_dict(brand: Brand) -> dict:
        return {
            "id": str(brand.id),
            "name_zh": brand.name_zh,
            "name_en": brand.name_en,
            "official_name": brand.official_name,
            "social_media_name": brand.social_media_name,
            "naming_notes": brand.naming_notes,
        }

    @staticmethod
    def _logo_to_dict(logo: BrandLogo) -> dict:
        return {
            "id": str(logo.id),
            "brand_id": str(logo.brand_id),
            "file_name": logo.file_name,
            "file_path": logo.file_path,
            "file_format": logo.file_format,
            "logo_type": logo.logo_type,
            "file_size_bytes": logo.file_size_bytes,
            "thumbnail_path": logo.thumbnail_path,
            "created_at": logo.created_at.isoformat() if logo.created_at else None,
        }
