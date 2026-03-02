from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.core.supabase import get_service_role_client
from app.dependencies.auth import require_admin


class PriestUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


router = APIRouter(prefix="/admin/priests", tags=["Admin Priests"])


# Update priest — {priest_id} is public.users.id where role='priest'
@router.put("/{priest_id}", status_code=200)
def update_priest(priest_id: str, update: PriestUpdate, current_user=Depends(require_admin)):
    client = get_service_role_client()

    # Verify priest exists in public.users
    existing_resp = (
        client.table("users")
        .select("id, email, first_name, last_name, phone, is_active")
        .eq("id", priest_id)
        .eq("role", "priest")
        .limit(1)
        .execute()
    )
    existing_rows = existing_resp.data or []
    if not existing_rows:
        raise HTTPException(status_code=404, detail="Priest not found.")
    existing = existing_rows[0]

    update_data = update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided.")

    # All editable fields live in public.users
    users_payload = {k: v for k, v in update_data.items() if k in ("first_name", "last_name", "phone", "email", "is_active")}
    users_resp = (
        client.table("users")
        .update(users_payload)
        .eq("id", priest_id)
        .execute()
    )
    if not users_resp.data:
        raise HTTPException(status_code=404, detail="Failed to update priest.")

    # Sync email to Supabase Auth only when it actually changed
    if "email" in update_data and update_data["email"] != existing.get("email"):
        try:
            client.auth.admin.update_user_by_id(priest_id, {"email": update_data["email"]})
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to update auth user email: {str(exc)}")

    return users_resp.data[0]


# Delete priest — {priest_id} is public.users.id where role='priest'
@router.delete("/{priest_id}", status_code=200)
def delete_priest(priest_id: str, current_user=Depends(require_admin)):
    client = get_service_role_client()

    # Verify priest exists
    existing_resp = (
        client.table("users")
        .select("id")
        .eq("id", priest_id)
        .eq("role", "priest")
        .limit(1)
        .execute()
    )
    if not (existing_resp.data or []):
        raise HTTPException(status_code=404, detail="Priest not found.")

    # Delete profile row (profiles.id = users.id)
    client.table("profiles").delete().eq("id", priest_id).execute()

    # Delete from public.users
    client.table("users").delete().eq("id", priest_id).execute()

    # Delete from Supabase Auth
    try:
        client.auth.admin.delete_user(priest_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to delete auth user: {str(exc)}")

    return {"message": "Priest deleted successfully"}

@router.get("/", summary="Get list of priests", description="Admin: List priests with pagination.")
def list_priests(
    current_user=Depends(require_admin),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    client = get_service_role_client()
    # Fetch priests from users table where role = 'priest'
    priests_resp = client.table("users") \
        .select("id, first_name, last_name, email, phone, is_active, created_at") \
        .eq("role", "priest") \
        .range(offset, offset + limit - 1) \
        .execute()
    priests = priests_resp.data or []

    # Get total count
    count_resp = client.table("users") \
        .select("id", count="exact") \
        .eq("role", "priest") \
        .execute()
    total = count_resp.count or 0

    # Collect priest IDs for batch queries
    priest_ids = [p["id"] for p in priests]

    # Fetch total bookings for each priest (orders.provider_id = priest id)
    bookings_map = {}
    if priest_ids:
        orders_resp = client.table("orders") \
            .select("provider_id") \
            .in_("provider_id", priest_ids) \
            .execute()
        for pid in priest_ids:
            bookings_map[pid] = sum(1 for o in (orders_resp.data or []) if o["provider_id"] == pid)

    # Fetch average rating for each priest (reviews.user_id = priest id)
    ratings_map = {}
    if priest_ids:
        reviews_resp = client.table("reviews") \
            .select("user_id, rating") \
            .in_("user_id", priest_ids) \
            .execute()
        for pid in priest_ids:
            ratings = [r["rating"] for r in (reviews_resp.data or []) if r["user_id"] == pid]
            ratings_map[pid] = round(sum(ratings) / len(ratings), 2) if ratings else None

    # Build response
    result = []
    for p in priests:
        result.append({
            "id": p["id"],
            "name": f"{p.get('first_name','')} {p.get('last_name','')}",
            "email": p.get("email"),
            "phone": p.get("phone"),
            "status": "active" if p.get("is_active") else "inactive",
            "created_at": p.get("created_at"),
            "total_bookings": bookings_map.get(p["id"], 0),
            "rating": ratings_map.get(p["id"]),
        })
    return {"priests": result, "total": total}
