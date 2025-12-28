from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_package import ServicePackage


async def get_all_service_packages(
    db: AsyncSession,
    service_id: Optional[UUID] = None,
) -> List[ServicePackage]:
    stmt = select(ServicePackage)

    if service_id:
        stmt = stmt.where(ServicePackage.service_id == service_id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_service_package_by_id(
    db: AsyncSession,
    package_id: UUID,
) -> Optional[ServicePackage]:
    stmt = select(ServicePackage).where(ServicePackage.id == package_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()