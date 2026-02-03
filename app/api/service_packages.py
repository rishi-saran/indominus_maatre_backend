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
    try:
        query = supabase.table("service_packages").select("*")

        if service_id:
            query = query.eq("service_id", str(service_id))

        response = query.execute()

        # ✅ Empty list is OK
        return response.data or []

    except Exception as e:
        print("Error in list_service_packages:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch service packages",
        )

    return response.data


@router.get("/{package_id}", response_model=ServicePackageOut)
def get_service_package(package_id: UUID):
    try:
        response = (
            supabase
            .table("service_packages")
            .select("*")
            .eq("id", str(package_id))
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Service package not found",
            )

        return response.data[0]

    except HTTPException:
        raise

    except Exception as e:
        print("Error in get_service_package:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch service package",
        )


    return response.data