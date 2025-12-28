from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.service_provider import (
    get_all_service_providers,
    get_service_provider_by_id,
)
from app.schemas.service_provider import ServiceProviderOut

router = APIRouter(
    tags=["Service Providers"]
)


@router.get("/", response_model=List[ServiceProviderOut])
async def list_service_providers(
    verified: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_service_providers(db, verified)


@router.get("/{provider_id}", response_model=ServiceProviderOut)
async def get_service_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    provider = await get_service_provider_by_id(db, provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail="Service provider not found")

    return provider