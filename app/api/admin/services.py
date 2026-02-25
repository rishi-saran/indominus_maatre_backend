from fastapi import APIRouter, Depends, status
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional

class AdminService(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    status: str

router = APIRouter(prefix="/admin/services", tags=["Admin Services"])

@router.get("/", response_model=List[AdminService])
def list_services(current_user=Depends(require_admin)):
    return []

@router.get("/{service_id}", response_model=AdminService)
def get_service(service_id: int, current_user=Depends(require_admin)):
    return {"id": service_id, "name": "Service Name", "price": 0.0, "status": "active"}

@router.post("/", response_model=AdminService, status_code=status.HTTP_201_CREATED)
def create_service(service: AdminService, current_user=Depends(require_admin)):
    return service

@router.put("/{service_id}", response_model=AdminService)
def update_service(service_id: int, service: AdminService, current_user=Depends(require_admin)):
    return service

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, current_user=Depends(require_admin)):
    return None
