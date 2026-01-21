from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import supabase
from app.schemas.service_provider import ServiceProviderOut

router = APIRouter(
    prefix="/service-providers",
    tags=["Service Providers"],
)


@router.get("/", response_model=List[ServiceProviderOut])
def list_service_providers(
    verified: Optional[bool] = Query(None),
):
    try:
        query = supabase.table("service_providers").select("*")

        if verified is not None:
            query = query.eq("verified", verified)

        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider_id}", response_model=ServiceProviderOut)
def get_service_provider(provider_id: UUID):
    try:
        response = (
            supabase
            .table("service_providers")
            .select("*")
            .eq("id", str(provider_id))
            .single()
            .execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Service provider not found")
        
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))