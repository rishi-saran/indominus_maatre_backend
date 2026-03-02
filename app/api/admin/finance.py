

from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import require_admin
from app.core.supabase import supabase
from typing import List

router = APIRouter(prefix="/admin/finance", tags=["Admin Finance"])


# Incoming Payments endpoint (latest orders)
@router.get("/incoming-payments")
def get_incoming_payments(current_user=Depends(require_admin), limit: int = 20):
    """Get latest orders for Incoming Payments section, joining users and payments."""
    # Fetch latest orders
    orders_resp = supabase.table("orders") \
        .select("id, user_id, total_amount, status, created_at") \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    orders = orders_resp.data or []

    # Collect user_ids and order_ids for batch fetching
    user_ids = list({o["user_id"] for o in orders if o.get("user_id")})
    order_ids = list({o["id"] for o in orders if o.get("id")})

    # Fetch users in batch
    users_map = {}
    if user_ids:
        users_resp = supabase.table("users") \
            .select("id, first_name, last_name") \
            .in_("id", user_ids) \
            .execute()
        for u in users_resp.data or []:
            full_name = ((u.get("first_name") or "") + " " + (u.get("last_name") or "")).strip()
            users_map[u["id"]] = full_name

    # Fetch payments in batch
    payments_map = {}
    if order_ids:
        payments_resp = supabase.table("payments") \
            .select("order_id, method") \
            .in_("order_id", order_ids) \
            .execute()
        for p in payments_resp.data or []:
            payments_map[p["order_id"]] = p.get("method")

    # Build results
    results = []
    for o in orders:
        results.append({
            "transaction_id": o.get("id"),
            "customer": users_map.get(o.get("user_id"), "Unknown"),
            "date": o.get("created_at"),
            "method": payments_map.get(o.get("id"), None),
            "amount": o.get("total_amount"),
            "status": o.get("status"),
        })
    return {"orders": results}

# Transactions endpoint
@router.get("/transactions")
def get_transactions(current_user=Depends(require_admin)):
    # Placeholder: Replace with DB query
    return {"transactions": []}

# Payouts endpoint
@router.get("/payouts")
def get_payouts(current_user=Depends(require_admin)):
    # Placeholder: Replace with DB query
    return {"payouts": []}

# Commission endpoint
@router.get("/commission")
def get_commission(current_user=Depends(require_admin)):
    # Placeholder: Replace with DB query
    return {"monthlyCommissionData": []}

from decimal import Decimal
# Summary endpoint
@router.get("/summary")
def get_summary(current_user=Depends(require_admin)):
    # Total revenue from orders
    orders_resp = supabase.table("orders") \
        .select("total_amount") \
        .execute()
    total_revenue = sum(Decimal(o["total_amount"]) for o in orders_resp.data or [])

    # Priest earnings from donations
    donations_resp = supabase.table("donations") \
        .select("amount") \
        .execute()
    priest_earnings = sum(Decimal(d["amount"]) for d in donations_resp.data or [])

    # Platform commission left as 0.0 for now
    platform_commission = 0.0

    return {
        "totalRevenue": float(total_revenue),
        "platformCommission": platform_commission,
        "priestEarnings": float(priest_earnings)
    }

# Approve payout endpoint
@router.post("/payouts/{id}/approve")
def approve_payout(id: str, current_user=Depends(require_admin)):
    # Placeholder: Replace with DB update
    return {"success": True, "id": id, "status": "approved"}

# Reject payout endpoint
@router.post("/payouts/{id}/reject")
def reject_payout(id: str, current_user=Depends(require_admin)):
    # Placeholder: Replace with DB update
    return {"success": True, "id": id, "status": "rejected"}
