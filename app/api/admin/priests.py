from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
class PriestUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str = None
    phone: str = None
    is_active: bool = None

from app.dependencies.auth import require_admin
from app.core.supabase import supabase

router = APIRouter(prefix="/admin/priests", tags=["Admin Priests"])


# Update priest details
@router.put("/{priest_id}", status_code=200)
def update_priest(priest_id: str, update: PriestUpdate, current_user=Depends(require_admin)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided.")
    resp = supabase.table("users").update(update_data).eq("id", priest_id).eq("role", "priest").execute()
    if resp.error:
        raise HTTPException(status_code=400, detail=resp.error['message'] if isinstance(resp.error, dict) and 'message' in resp.error else str(resp.error))
    if not resp.data:
        raise HTTPException(status_code=404, detail="Priest not found or not updated.")
    return {"success": True, "updated": resp.data}

# Delete priest
@router.delete("/{priest_id}", status_code=200)
def delete_priest(priest_id: str, current_user=Depends(require_admin)):
    resp = supabase.table("users").delete().eq("id", priest_id).eq("role", "priest").execute()
    if resp.error:
        raise HTTPException(status_code=400, detail=resp.error['message'] if isinstance(resp.error, dict) and 'message' in resp.error else str(resp.error))
    if not resp.data:
        raise HTTPException(status_code=404, detail="Priest not found or not deleted.")
    return {"success": True, "deleted": resp.data}

@router.get("/", summary="Get list of priests", description="Admin: List priests with pagination.")
def list_priests(
    current_user=Depends(require_admin),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    # Fetch priests from users table where role = 'priest'
    priests_resp = supabase.table("users") \
        .select("id, first_name, last_name, email, phone, is_active, created_at") \
        .eq("role", "priest") \
        .range(offset, offset + limit - 1) \
        .execute()
    priests = priests_resp.data or []

    # Get total count
    count_resp = supabase.table("users") \
        .select("id", count="exact") \
        .eq("role", "priest") \
        .execute()
    total = count_resp.count or 0

    # Collect priest IDs for batch queries
    priest_ids = [p["id"] for p in priests]

    # Fetch total bookings for each priest (orders.provider_id = priest id)
    bookings_map = {}
    if priest_ids:
        orders_resp = supabase.table("orders") \
            .select("provider_id") \
            .in_("provider_id", priest_ids) \
            .execute()
        for pid in priest_ids:
            bookings_map[pid] = sum(1 for o in (orders_resp.data or []) if o["provider_id"] == pid)

    # Fetch average rating for each priest (reviews.user_id = priest id)
    ratings_map = {}
    if priest_ids:
        reviews_resp = supabase.table("reviews") \
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
