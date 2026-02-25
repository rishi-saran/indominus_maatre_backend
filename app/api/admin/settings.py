from fastapi import APIRouter, Depends, status
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional

class AdminSetting(BaseModel):
    key: str
    value: str

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])

@router.get("/", response_model=List[AdminSetting])
def list_settings(current_user=Depends(require_admin)):
    return []

@router.get("/{key}", response_model=AdminSetting)
def get_setting(key: str, current_user=Depends(require_admin)):
    return {"key": key, "value": "sample"}

@router.post("/", response_model=AdminSetting, status_code=status.HTTP_201_CREATED)
def create_setting(setting: AdminSetting, current_user=Depends(require_admin)):
    return setting

@router.put("/{key}", response_model=AdminSetting)
def update_setting(key: str, setting: AdminSetting, current_user=Depends(require_admin)):
    return setting

@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_setting(key: str, current_user=Depends(require_admin)):
    return None
