from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.service_category import get_all_categories
from app.schemas.service_category import ServiceCategoryOut

router = APIRouter(prefix="/service-categories", tags=["Service Categories"])

@router.get("/", response_model=list[ServiceCategoryOut])
async def list_service_categories(db: AsyncSession = Depends(get_db)):
    return await get_all_categories(db)