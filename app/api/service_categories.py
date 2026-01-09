from fastapi import APIRouter, HTTPException

from app.core.supabase import supabase
from app.schemas.service_category import ServiceCategoryOut

router = APIRouter(
    prefix="/service-categories",
    tags=["Service Categories"],
)

@router.get("/", response_model=list[ServiceCategoryOut])
def list_service_categories():
    response = (
        supabase
        .table("service_categories")
        .select("*")
        .order("name")
        .execute()
    )

    if response.error:
        raise HTTPException(
            status_code=500,
            detail=response.error.message
        )

    return response.data