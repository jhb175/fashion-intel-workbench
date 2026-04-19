"""Admin management API router — sources, brands, keywords, monitor groups."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.keyword import Keyword
from app.models.monitor_group import MonitorGroup
from app.models.source import Source
from app.models.user import User
from app.responses import success_response
from app.schemas.admin import (
    BrandCreateRequest,
    BrandLogoUpdateRequest,
    BrandUpdateRequest,
    KeywordCreateRequest,
    KeywordUpdateRequest,
    MonitorGroupUpdateRequest,
    SourceCreateRequest,
    SourceUpdateRequest,
)
from app.services.brand_service import BrandService
from app.services.file_storage_service import FileStorageService
from app.utils.auth import get_current_user
from app.utils.errors import NotFoundError

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_brand_service(db: AsyncSession = Depends(get_db)) -> BrandService:
    return BrandService(db=db)


def _get_file_storage_service() -> FileStorageService:
    return FileStorageService()


# ===========================================================================
# Sources
# ===========================================================================


@router.get("/sources")
async def list_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get source list with pagination."""
    count_stmt = select(func.count()).select_from(Source)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(Source)
        .order_by(Source.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    sources = list(result.scalars().all())

    return success_response(data={
        "items": [_source_to_dict(s) for s in sources],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/sources")
async def create_source(
    body: SourceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a new source."""
    source = Source(
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        monitor_group_id=body.monitor_group_id,
        is_enabled=body.is_enabled,
        collect_interval_minutes=body.collect_interval_minutes,
        config=body.config,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return success_response(data=_source_to_dict(source))


@router.put("/sources/{source_id}")
async def update_source(
    source_id: uuid.UUID,
    body: SourceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Edit an existing source."""
    source = await _get_source_or_404(db, source_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
    await db.flush()
    await db.refresh(source)
    return success_response(data=_source_to_dict(source))


@router.patch("/sources/{source_id}/toggle")
async def toggle_source(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Enable/disable a source."""
    source = await _get_source_or_404(db, source_id)
    source.is_enabled = not source.is_enabled
    await db.flush()
    await db.refresh(source)
    return success_response(data=_source_to_dict(source))


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a source."""
    source = await _get_source_or_404(db, source_id)
    await db.delete(source)
    await db.flush()
    return success_response(message="资讯源已删除")


# ===========================================================================
# Brands
# ===========================================================================


@router.get("/brands")
async def list_brands(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    monitor_group_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: BrandService = Depends(_get_brand_service),
) -> dict:
    """Get brand pool list with pagination."""
    result = await service.list_brands(page=page, page_size=page_size, monitor_group_id=monitor_group_id)
    return success_response(data=result)


@router.post("/brands")
async def create_brand(
    body: BrandCreateRequest,
    current_user: User = Depends(get_current_user),
    service: BrandService = Depends(_get_brand_service),
) -> dict:
    """Add a new brand."""
    brand = await service.create_brand(body.model_dump())
    return success_response(data=brand)


@router.put("/brands/{brand_id}")
async def update_brand(
    brand_id: uuid.UUID,
    body: BrandUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: BrandService = Depends(_get_brand_service),
) -> dict:
    """Edit an existing brand."""
    brand = await service.update_brand(brand_id, body.model_dump(exclude_unset=True))
    return success_response(data=brand)


@router.delete("/brands/{brand_id}")
async def delete_brand(
    brand_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BrandService = Depends(_get_brand_service),
) -> dict:
    """Delete a brand."""
    await service.delete_brand(brand_id)
    return success_response(message="品牌已删除")


@router.get("/brands/search-naming")
async def search_brand_naming(
    q: str = Query("", description="Search query for brand naming"),
    current_user: User = Depends(get_current_user),
    service: BrandService = Depends(_get_brand_service),
) -> dict:
    """Search brand naming (fuzzy match)."""
    results = await service.search_naming(q)
    return success_response(data=results)


# ===========================================================================
# Brand Logos
# ===========================================================================


@router.get("/brands/{brand_id}/logos")
async def list_brand_logos(
    brand_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BrandService = Depends(_get_brand_service),
) -> dict:
    """Get brand logo list."""
    logos = await service.list_logos(brand_id)
    return success_response(data=logos)


@router.post("/brands/{brand_id}/logos")
async def upload_brand_logo(
    brand_id: uuid.UUID,
    file: UploadFile = File(...),
    logo_type: str = Form("main"),
    current_user: User = Depends(get_current_user),
    brand_service: BrandService = Depends(_get_brand_service),
    file_service: FileStorageService = Depends(_get_file_storage_service),
) -> dict:
    """Upload a brand logo (multipart/form-data)."""
    # Validate logo_type
    file_service.validate_logo_type(logo_type)

    # Validate file format
    file_service.validate_file_format(file.filename or "")

    # Read file content
    content = await file.read()

    # Save to disk
    storage_info = await file_service.save_upload(
        brand_id=brand_id,
        filename=file.filename or "upload.png",
        file_content=content,
    )

    # Create DB record
    logo_data = {
        "file_name": file.filename or "upload.png",
        "file_path": storage_info["file_path"],
        "file_format": storage_info["file_format"],
        "logo_type": logo_type,
        "file_size_bytes": storage_info["file_size_bytes"],
        "thumbnail_path": storage_info["thumbnail_path"],
    }
    logo = await brand_service.create_logo(brand_id, logo_data)
    return success_response(data=logo)


@router.put("/brands/{brand_id}/logos/{logo_id}")
async def update_brand_logo(
    brand_id: uuid.UUID,
    logo_id: uuid.UUID,
    body: BrandLogoUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: BrandService = Depends(_get_brand_service),
) -> dict:
    """Update logo metadata."""
    logo = await service.update_logo(brand_id, logo_id, body.model_dump(exclude_unset=True))
    return success_response(data=logo)


@router.delete("/brands/{brand_id}/logos/{logo_id}")
async def delete_brand_logo(
    brand_id: uuid.UUID,
    logo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    brand_service: BrandService = Depends(_get_brand_service),
    file_service: FileStorageService = Depends(_get_file_storage_service),
) -> dict:
    """Delete a brand logo."""
    file_path = await brand_service.delete_logo(brand_id, logo_id)
    # Clean up file from disk
    file_service.delete_file(file_path)
    return success_response(message="Logo 已删除")


@router.get("/brands/{brand_id}/logos/{logo_id}/download")
async def download_brand_logo(
    brand_id: uuid.UUID,
    logo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    brand_service: BrandService = Depends(_get_brand_service),
    file_service: FileStorageService = Depends(_get_file_storage_service),
) -> FileResponse:
    """Download brand logo file."""
    logo = await brand_service.get_logo(brand_id, logo_id)
    file_path = file_service.get_file_path(logo["file_path"])
    return FileResponse(
        path=str(file_path),
        filename=logo["file_name"],
        media_type="application/octet-stream",
    )


# ===========================================================================
# Keywords
# ===========================================================================


@router.get("/keywords")
async def list_keywords(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    monitor_group_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get keyword pool list with pagination."""
    count_stmt = select(func.count()).select_from(Keyword)
    if monitor_group_id is not None:
        count_stmt = count_stmt.where(Keyword.monitor_group_id == monitor_group_id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = select(Keyword).order_by(Keyword.created_at.desc())
    if monitor_group_id is not None:
        stmt = stmt.where(Keyword.monitor_group_id == monitor_group_id)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    keywords = list(result.scalars().all())

    return success_response(data={
        "items": [_keyword_to_dict(k) for k in keywords],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/keywords")
async def create_keyword(
    body: KeywordCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a new keyword."""
    keyword = Keyword(
        word_zh=body.word_zh,
        word_en=body.word_en,
        monitor_group_id=body.monitor_group_id,
    )
    db.add(keyword)
    await db.flush()
    await db.refresh(keyword)
    return success_response(data=_keyword_to_dict(keyword))


@router.put("/keywords/{keyword_id}")
async def update_keyword(
    keyword_id: uuid.UUID,
    body: KeywordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Edit an existing keyword."""
    keyword = await _get_keyword_or_404(db, keyword_id)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(keyword, field, value)
    await db.flush()
    await db.refresh(keyword)
    return success_response(data=_keyword_to_dict(keyword))


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(
    keyword_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a keyword."""
    keyword = await _get_keyword_or_404(db, keyword_id)
    await db.delete(keyword)
    await db.flush()
    return success_response(message="关键词已删除")


# ===========================================================================
# Monitor Groups
# ===========================================================================


@router.get("/monitor-groups")
async def list_monitor_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get monitor group list."""
    stmt = select(MonitorGroup).order_by(MonitorGroup.sort_order)
    result = await db.execute(stmt)
    groups = list(result.scalars().all())

    data = []
    for g in groups:
        data.append({
            "id": str(g.id),
            "name": g.name,
            "display_name": g.display_name,
            "description": g.description,
            "sort_order": g.sort_order,
            "source_count": len(g.sources) if g.sources else 0,
            "brand_count": len(g.brands) if g.brands else 0,
            "keyword_count": len(g.keywords) if g.keywords else 0,
            "created_at": g.created_at.isoformat() if g.created_at else None,
            "updated_at": g.updated_at.isoformat() if g.updated_at else None,
        })

    return success_response(data=data)


@router.put("/monitor-groups/{group_id}")
async def update_monitor_group(
    group_id: uuid.UUID,
    body: MonitorGroupUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Edit a monitor group."""
    stmt = select(MonitorGroup).where(MonitorGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalar_one_or_none()
    if group is None:
        raise NotFoundError("监控组不存在")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    await db.flush()
    await db.refresh(group)

    return success_response(data={
        "id": str(group.id),
        "name": group.name,
        "display_name": group.display_name,
        "description": group.description,
        "sort_order": group.sort_order,
        "source_count": len(group.sources) if group.sources else 0,
        "brand_count": len(group.brands) if group.brands else 0,
        "keyword_count": len(group.keywords) if group.keywords else 0,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "updated_at": group.updated_at.isoformat() if group.updated_at else None,
    })


# ===========================================================================
# Helper functions
# ===========================================================================


async def _get_source_or_404(db: AsyncSession, source_id: uuid.UUID) -> Source:
    stmt = select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()
    if source is None:
        raise NotFoundError("资讯源不存在")
    return source


async def _get_keyword_or_404(db: AsyncSession, keyword_id: uuid.UUID) -> Keyword:
    stmt = select(Keyword).where(Keyword.id == keyword_id)
    result = await db.execute(stmt)
    keyword = result.scalar_one_or_none()
    if keyword is None:
        raise NotFoundError("关键词不存在")
    return keyword


def _source_to_dict(source: Source) -> dict:
    return {
        "id": str(source.id),
        "name": source.name,
        "url": source.url,
        "source_type": source.source_type,
        "monitor_group_id": str(source.monitor_group_id) if source.monitor_group_id else None,
        "is_enabled": source.is_enabled,
        "collect_interval_minutes": source.collect_interval_minutes,
        "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
        "last_collect_status": source.last_collect_status,
        "last_error_message": source.last_error_message,
        "config": source.config,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }


def _keyword_to_dict(keyword: Keyword) -> dict:
    return {
        "id": str(keyword.id),
        "word_zh": keyword.word_zh,
        "word_en": keyword.word_en,
        "monitor_group_id": str(keyword.monitor_group_id) if keyword.monitor_group_id else None,
        "created_at": keyword.created_at.isoformat() if keyword.created_at else None,
        "updated_at": keyword.updated_at.isoformat() if keyword.updated_at else None,
    }


# ===========================================================================
# Manual Collection Trigger (no Celery needed)
# ===========================================================================


@router.post("/collect")
async def trigger_collection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger article collection from all enabled sources.

    This runs synchronously (no Celery) — useful for local dev on Windows.
    """
    from app.services.aggregation_service import AggregationService

    service = AggregationService(db)
    summary = await service.run_collection()
    return success_response(data=summary)


@router.post("/collect/{source_id}")
async def trigger_source_collection(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger collection from a single source."""
    from app.services.aggregation_service import AggregationService

    service = AggregationService(db)
    result = await service.collect_single_source(source_id)
    return success_response(data=result)
