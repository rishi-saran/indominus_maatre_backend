

from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import require_admin
from app.core.supabase import supabase
from typing import List
from collections import defaultdict

router = APIRouter(prefix="/admin/finance", tags=["Admin Finance"])

# Priest payouts list
@router.get("/priest-payouts")
def get_priest_payouts(current_user=Depends(require_admin), limit: int = 50):
    """Return rows from donations joined to users and session."""
    # Fetch donations
    donations_resp = supabase.table("donations") \
        .select("id, priest_id, customer_id, amount, created_at, call_id") \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    donations = donations_resp.data or []

    # Collect priest_ids, customer_ids, call_ids
    priest_ids = list({d["priest_id"] for d in donations if d.get("priest_id")})
    customer_ids = list({d["customer_id"] for d in donations if d.get("customer_id")})
    call_ids = list({d["call_id"] for d in donations if d.get("call_id")})

    # Fetch users in batch
    users_map = {}
    if priest_ids or customer_ids:
        all_ids = list(set(priest_ids + customer_ids))
        users_resp = supabase.table("users") \
            .select("id, first_name, last_name") \
            .in_("id", all_ids) \
            .execute()
        for u in users_resp.data or []:
            full_name = ((u.get("first_name") or "") + " " + (u.get("last_name") or "")).strip()
            users_map[u["id"]] = full_name

    # Fetch sessions in batch (sessions.stream_id = donations.call_id)
    sessions_map = {}
    if call_ids:
        sessions_resp = supabase.table("sessions") \
            .select("id, stream_id") \
            .in_("stream_id", call_ids) \
            .execute()
        for s in sessions_resp.data or []:
            sessions_map[s["stream_id"]] = s["id"]

    # Build results
    results = []
    for d in donations:
        results.append({
            "id": d.get("id"),
            "priest_name": users_map.get(d.get("priest_id"), "Unknown"),
            "customer_name": users_map.get(d.get("customer_id"), "Unknown"),
            "amount": float(d.get("amount", 0)),
            "created_at": d.get("created_at"),
            "call_id": d.get("call_id"),
            "session_id": sessions_map.get(d.get("call_id")),
            "status": "processed"  # Placeholder, update if you have payout status
        })
    return {"payouts": results}

# Priest earnings summary
@router.get("/priest-earnings")
def get_priest_earnings(current_user=Depends(require_admin)):
    """Group by priest, sum total amount."""
    # Fetch all donations
    donations_resp = supabase.table("donations") \
        .select("priest_id, amount") \
        .execute()
    donations = donations_resp.data or []

    # Fetch priest names
    priest_ids = list({d["priest_id"] for d in donations if d.get("priest_id")})
    users_map = {}
    if priest_ids:
        users_resp = supabase.table("users") \
            .select("id, first_name, last_name") \
            .in_("id", priest_ids) \
            .execute()
        for u in users_resp.data or []:
            full_name = ((u.get("first_name") or "") + " " + (u.get("last_name") or "")).strip()
            users_map[u["id"]] = full_name

    # Group and sum
    earnings = defaultdict(float)
    for d in donations:
        pid = d.get("priest_id")
        if pid:
            earnings[pid] += float(d.get("amount", 0))

    # Build results
    results = []
    for pid, total in earnings.items():
        results.append({
            "priest_name": users_map.get(pid, "Unknown"),
            "total_amount": total
        })
    return {"earnings": results}



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
