"""Knowledge base API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.responses import success_response
from app.schemas.knowledge import (
    KnowledgeCategory,
    KnowledgeEntryCreateRequest,
    KnowledgeEntryUpdateRequest,
)
from app.services.knowledge_service import KnowledgeService
from app.utils.auth import get_current_user

router = APIRouter(tags=["knowledge"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db=db)


# ===========================================================================
# Knowledge entry endpoints
# ===========================================================================


@router.get("/api/v1/knowledge")
async def list_knowledge_entries(
    category: KnowledgeCategory | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_knowledge_service),
) -> dict:
    """Get knowledge entry list with optional category and keyword filtering."""
    result = await service.list_entries(
        category=category.value if category else None,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/api/v1/knowledge/{entry_id}")
async def get_knowledge_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_knowledge_service),
) -> dict:
    """Get a single knowledge entry by ID."""
    entry = await service.get_entry(entry_id)
    return success_response(data=entry.model_dump(mode="json"))


@router.post("/api/v1/knowledge")
async def create_knowledge_entry(
    body: KnowledgeEntryCreateRequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_knowledge_service),
) -> dict:
    """Create a new knowledge entry."""
    entry = await service.create_entry(body)
    return success_response(data=entry.model_dump(mode="json"))


@router.put("/api/v1/knowledge/{entry_id}")
async def update_knowledge_entry(
    entry_id: uuid.UUID,
    body: KnowledgeEntryUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_knowledge_service),
) -> dict:
    """Update an existing knowledge entry."""
    entry = await service.update_entry(entry_id, body)
    return success_response(data=entry.model_dump(mode="json"))


@router.delete("/api/v1/knowledge/{entry_id}")
async def delete_knowledge_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: KnowledgeService = Depends(_get_knowledge_service),
) -> dict:
    """Delete a knowledge entry."""
    await service.delete_entry(entry_id)
    return success_response(message="知识条目已删除")
