from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.service import Service


async def get_all_services(
    db: AsyncSession,
    category_id: Optional[UUID] = None
) -> List[Service]:
    stmt = select(Service)

    if category_id:
        stmt = stmt.where(Service.category_id == category_id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_service_by_id(
    db: AsyncSession,
    service_id: UUID
) -> Optional[Service]:
    stmt = select(Service).where(Service.id == service_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()