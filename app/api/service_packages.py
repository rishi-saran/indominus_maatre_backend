from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.service_package import (
    get_all_service_packages,
    get_service_package_by_id,
)
from app.schemas.service_package import ServicePackageOut

router = APIRouter(
    prefix="/service-packages",
    tags=["Service Packages"],
)


@router.get("/", response_model=List[ServicePackageOut])
async def list_service_packages(
    service_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_service_packages(db, service_id)


@router.get("/{package_id}", response_model=ServicePackageOut)
async def get_service_package(
    package_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    package = await get_service_package_by_id(db, package_id)

    if not package:
        raise HTTPException(status_code=404, detail="Service package not found")

    return package