from fastapi import APIRouter, Depends, status
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional

class AdminPriest(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    status: str

router = APIRouter(prefix="/admin/priests", tags=["Admin Priests"])

@router.get("/", response_model=List[AdminPriest])
def list_priests(current_user=Depends(require_admin)):
    return []

@router.get("/{priest_id}", response_model=AdminPriest)
def get_priest(priest_id: int, current_user=Depends(require_admin)):
    return {"id": priest_id, "name": "Priest Name", "email": "priest@example.com", "status": "active"}

@router.post("/", response_model=AdminPriest, status_code=status.HTTP_201_CREATED)
def create_priest(priest: AdminPriest, current_user=Depends(require_admin)):
    return priest

@router.put("/{priest_id}", response_model=AdminPriest)
def update_priest(priest_id: int, priest: AdminPriest, current_user=Depends(require_admin)):
    return priest

@router.delete("/{priest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_priest(priest_id: int, current_user=Depends(require_admin)):
    return None
