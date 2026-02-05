from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import supabase
from app.schemas.service_addon import ServiceAddonOut

router = APIRouter(
    prefix="/service-addons",
    tags=["Service Addons"],
)


@router.get("/", response_model=List[ServiceAddonOut])
def list_service_addons(
    service_id: Optional[UUID] = Query(None),
):
    query = supabase.table("service_addons").select("*")

    if service_id:
        query = query.eq("service_id", str(service_id))

    try:
        response = query.execute()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch service addons: {exc}",
        )

    response_error = getattr(response, "error", None)
    if response_error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch service addons: {response_error}",
        )

    return response.data or []


@router.get("/{addon_id}", response_model=ServiceAddonOut)
def get_service_addon(addon_id: UUID):
    try:
        response = (
            supabase
            .table("service_addons")
            .select("*")
            .eq("id", str(addon_id))
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch service addon: {exc}",
        )

    response_error = getattr(response, "error", None)
    if response_error or not response.data:
        raise HTTPException(
            status_code=404,
            detail="Service addon not found",
        )

    return response.data