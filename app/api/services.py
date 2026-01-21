from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import supabase
from app.schemas.service import ServiceBase

router = APIRouter(
    prefix="/services",
    tags=["Services"],
)


@router.get("/", response_model=List[ServiceBase])
def list_services(
    category_id: Optional[UUID] = Query(None),
):
    try:
        query = supabase.table("services").select("*")

        if category_id:
            query = query.eq("category_id", str(category_id))

        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error in list_services: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch services: {str(e)}"
        )


@router.get("/{service_id}", response_model=ServiceBase)
def get_service(service_id: UUID):
    response = (
        supabase
        .table("services")
        .select("*")
        .eq("id", str(service_id))
        .execute()
    )

    if response.error:
        raise HTTPException(
            status_code=500,
            detail=response.error.message,
        )

    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Service not found")

    return response.data[0]