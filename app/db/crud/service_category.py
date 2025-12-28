from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.service_category import ServiceCategory

async def get_all_categories(db: AsyncSession):
    result = await db.execute(select(ServiceCategory))
    return result.scalars().all()