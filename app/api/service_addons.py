from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.service_addon import (
    get_all_service_addons,
    get_service_addon_by_id,
)
from app.schemas.service_addon import ServiceAddonOut

router = APIRouter(
    tags=["Service Addons"]
)


@router.get("/", response_model=List[ServiceAddonOut])
async def list_service_addons(
    service_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_service_addons(db, service_id)


@router.get("/{addon_id}", response_model=ServiceAddonOut)
async def get_service_addon(
    addon_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    addon = await get_service_addon_by_id(db, addon_id)

    if not addon:
        raise HTTPException(status_code=404, detail="Service addon not found")

    return addon