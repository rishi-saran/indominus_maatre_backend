from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.service import get_all_services, get_service_by_id
from app.schemas.service import ServiceBase

router = APIRouter(
    tags=["Services"]
)


@router.get("/", response_model=List[ServiceBase])
async def list_services(
    category_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_services(db, category_id)


@router.get("/{service_id}", response_model=ServiceBase)
async def get_service(
    service_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = await get_service_by_id(db, service_id)

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return service