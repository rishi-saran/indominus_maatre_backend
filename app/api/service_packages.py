from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import supabase
from app.schemas.service_package import ServicePackageOut

router = APIRouter(
    prefix="/service-packages",
    tags=["Service Packages"],
)


@router.get("/", response_model=List[ServicePackageOut])
def list_service_packages(
    service_id: Optional[UUID] = Query(None),
):
    query = supabase.table("service_packages").select("*")

    if service_id:
        query = query.eq("service_id", str(service_id))

    response = query.execute()

    if response.error:
        raise HTTPException(
            status_code=500,
            detail=response.error.message,
        )

    return response.data


@router.get("/{package_id}", response_model=ServicePackageOut)
def get_service_package(package_id: UUID):
    response = (
        supabase
        .table("service_packages")
        .select("*")
        .eq("id", str(package_id))
        .single()
        .execute()
    )

    if response.error:
        if response.error.code == "PGRST116":
            raise HTTPException(
                status_code=404,
                detail="Service package not found",
            )

        raise HTTPException(
            status_code=500,
            detail=response.error.message,
        )

    return response.data