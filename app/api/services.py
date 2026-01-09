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
    query = supabase.table("services").select("*")

    if category_id:
        query = query.eq("category_id", str(category_id))

    response = query.execute()

    if response.error:
        raise HTTPException(
            status_code=500,
            detail=response.error.message,
        )

    return response.data


@router.get("/{service_id}", response_model=ServiceBase)
def get_service(service_id: UUID):
    response = (
        supabase
        .table("services")
        .select("*")
        .eq("id", str(service_id))
        .single()
        .execute()
    )

    if response.error:
        # Not found
        if response.error.code == "PGRST116":
            raise HTTPException(status_code=404, detail="Service not found")

        raise HTTPException(
            status_code=500,
            detail=response.error.message,
        )

    return response.data