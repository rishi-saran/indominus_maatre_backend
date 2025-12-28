from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_addon import ServiceAddon


async def get_all_service_addons(
    db: AsyncSession,
    service_id: Optional[UUID] = None,
) -> List[ServiceAddon]:
    stmt = select(ServiceAddon)

    if service_id:
        stmt = stmt.where(ServiceAddon.service_id == service_id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_service_addon_by_id(
    db: AsyncSession,
    addon_id: UUID,
) -> Optional[ServiceAddon]:
    stmt = select(ServiceAddon).where(ServiceAddon.id == addon_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()