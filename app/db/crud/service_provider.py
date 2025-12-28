from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_provider import ServiceProvider


async def get_all_service_providers(
    db: AsyncSession,
    verified: Optional[bool] = None,
) -> List[ServiceProvider]:
    stmt = select(ServiceProvider)

    if verified is not None:
        stmt = stmt.where(ServiceProvider.verified == verified)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_service_provider_by_id(
    db: AsyncSession,
    provider_id: UUID,
) -> Optional[ServiceProvider]:
    stmt = select(ServiceProvider).where(ServiceProvider.id == provider_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()