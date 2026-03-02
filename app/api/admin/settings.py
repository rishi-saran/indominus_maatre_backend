from typing import Dict, List, Union

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator

from app.core.supabase import get_service_role_client
from app.dependencies.auth import require_admin


class AdminSetting(BaseModel):
    key: str
    value: str


class BulkSettingsPayload(BaseModel):
    """
    Accepts either:
      { "settings": { "platform_commission_rate": "15", "payout_threshold": "5000" } }  (frontend-friendly dict)
    or:
      { "settings": [{ "key": "platform_commission_rate", "value": "15" }, ...] }  (array)
    """
    settings: Union[Dict[str, str], List[AdminSetting]]

    def to_rows(self) -> List[dict]:
        if isinstance(self.settings, dict):
            return [{"key": k, "value": v} for k, v in self.settings.items()]
        return [{"key": s.key, "value": s.value} for s in self.settings]


# Canonical commission/platform setting keys
COMMISSION_KEYS = [
    "platform_commission_rate",
    "payout_threshold",
]

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])


@router.get("/", response_model=List[AdminSetting])
def list_settings(current_user=Depends(require_admin)):
    client = get_service_role_client()
    resp = client.table("settings").select("key, value").order("key").execute()
    return resp.data or []


@router.get("/commission", response_model=List[AdminSetting])
def get_commission_settings(current_user=Depends(require_admin)):
    """Returns only the commission/platform-fee related settings."""
    client = get_service_role_client()
    resp = (
        client.table("settings")
        .select("key, value")
        .in_("key", COMMISSION_KEYS)
        .execute()
    )
    rows = {r["key"]: r["value"] for r in (resp.data or [])}
    return [{"key": k, "value": rows.get(k, "")} for k in COMMISSION_KEYS]


@router.get("/{key}", response_model=AdminSetting)
def get_setting(key: str, current_user=Depends(require_admin)):
    client = get_service_role_client()
    resp = client.table("settings").select("key, value").eq("key", key).limit(1).execute()
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found.")
    return rows[0]


@router.put("/{key}", response_model=AdminSetting)
def upsert_setting(key: str, setting: AdminSetting, current_user=Depends(require_admin)):
    """Create or update a setting by key (upsert)."""
    client = get_service_role_client()
    resp = (
        client.table("settings")
        .upsert({"key": key, "value": setting.value}, on_conflict="key")
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to upsert setting.")
    return resp.data[0]


@router.post("/bulk", response_model=List[AdminSetting])
def bulk_upsert_settings(payload: BulkSettingsPayload, current_user=Depends(require_admin)):
    """Upsert multiple settings at once — useful for saving commission rates form."""
    client = get_service_role_client()
    rows = payload.to_rows()
    resp = client.table("settings").upsert(rows, on_conflict="key").execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to bulk upsert settings.")
    return resp.data


@router.delete("/{key}", status_code=200)
def delete_setting(key: str, current_user=Depends(require_admin)):
    client = get_service_role_client()
    resp = client.table("settings").delete().eq("key", key).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found.")
    return {"message": f"Setting '{key}' deleted."}
