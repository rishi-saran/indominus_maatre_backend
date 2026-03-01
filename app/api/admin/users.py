"""
Admin Users management endpoints.
Handles listing, creating, updating, and deleting admin users.
Role enum values: customer | priest | admin  (no sub-roles).
All admins are treated equally — no super_admin / editor / viewer distinction.
Create-admin flow: plain_password (same pattern as priest onboarding).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.core.supabase import get_service_role_client
from app.dependencies.auth import require_admin


class AdminUserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    plain_password: str


class AdminUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get("/")
def list_admin_users(
    current_user=Depends(require_admin),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all users with role=admin."""
    client = get_service_role_client()
    resp = (
        client.table("users")
        .select("id, first_name, last_name, email, phone, is_active, created_at")
        .eq("role", "admin")
        .range(offset, offset + limit - 1)
        .execute()
    )
    count_resp = (
        client.table("users")
        .select("id", count="exact")
        .eq("role", "admin")
        .execute()
    )
    return {"users": resp.data or [], "total": count_resp.count or 0}


@router.post("/", status_code=201)
def create_admin_user(payload: AdminUserCreate, current_user=Depends(require_admin)):
    """
    Create a new admin user with a plain password.
    Same flow as priest onboarding:
      1. Create in Supabase Auth (email_confirm=True, no magic link)
      2. Insert into public.users with role='admin'
      3. Insert into public.profiles
    """
    client = get_service_role_client()

    # Guard: prevent duplicate
    existing = (
        client.table("users")
        .select("id")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    # 1. Create Supabase Auth user (service-role, no session side-effects)
    try:
        auth_result = client.auth.admin.create_user({
            "email": payload.email,
            "password": payload.plain_password,
            "email_confirm": True,
        })
        auth_user = auth_result.user
        if not auth_user:
            raise Exception("Supabase Auth user creation returned no user.")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Auth creation failed: {str(exc)}")

    uid = auth_user.id

    # 2. Upsert into public.users — overwrites the trigger-created row (role='customer')
    try:
        users_resp = client.table("users").upsert({
            "id": uid,
            "email": payload.email,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "phone": payload.phone,
            "is_active": True,
            "role": "admin",
        }, on_conflict="id").execute()
        if not users_resp.data:
            raise Exception("Upsert into public.users returned no data.")
    except Exception as exc:
        # Roll back: delete auth user and any trigger-created users row
        try:
            client.table("users").delete().eq("id", uid).execute()
        except Exception:
            pass
        try:
            client.auth.admin.delete_user(uid)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to create admin user record: {str(exc)}")

    # 3. Upsert into public.profiles (handles trigger-created rows)
    try:
        client.table("profiles").upsert({"id": uid, "role": "admin"}, on_conflict="id").execute()
    except Exception:
        # Non-fatal: profile row missing won't break auth
        pass

    return users_resp.data[0]


@router.put("/{user_id}", status_code=200)
def update_admin_user(
    user_id: str, update: AdminUserUpdate, current_user=Depends(require_admin)
):
    """Update an admin user's details. Syncs email to Supabase Auth if changed."""
    client = get_service_role_client()

    existing_resp = (
        client.table("users")
        .select("id, email")
        .eq("id", user_id)
        .eq("role", "admin")
        .limit(1)
        .execute()
    )
    existing_rows = existing_resp.data or []
    if not existing_rows:
        raise HTTPException(status_code=404, detail="Admin user not found.")
    existing_email = existing_rows[0].get("email")

    update_data = update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided.")

    users_resp = (
        client.table("users")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )
    if not users_resp.data:
        raise HTTPException(status_code=404, detail="Failed to update admin user.")

    # Sync email to auth only when it changed
    if "email" in update_data and update_data["email"] != existing_email:
        try:
            client.auth.admin.update_user_by_id(user_id, {"email": update_data["email"]})
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Failed to update auth user email: {str(exc)}"
            )

    return users_resp.data[0]


@router.delete("/{user_id}", status_code=200)
def delete_admin_user(user_id: str, current_user=Depends(require_admin)):
    """Cascade delete: public.profiles → public.users → Supabase Auth."""
    client = get_service_role_client()

    existing_resp = (
        client.table("users")
        .select("id")
        .eq("id", user_id)
        .eq("role", "admin")
        .limit(1)
        .execute()
    )
    if not (existing_resp.data or []):
        raise HTTPException(status_code=404, detail="Admin user not found.")

    client.table("profiles").delete().eq("id", user_id).execute()
    client.table("users").delete().eq("id", user_id).execute()

    try:
        client.auth.admin.delete_user(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to delete auth user: {str(exc)}"
        )

    return {"message": "Admin user deleted successfully"}
