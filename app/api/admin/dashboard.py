
from fastapi import APIRouter, Depends
from app.dependencies.auth import require_admin
from app.core.supabase import supabase
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])

@router.get("/revenue")
def get_revenue(current_user=Depends(require_admin)):
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")
    previous_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    # Sum revenue for current month
    current_month_resp = supabase.table("orders") \
        .select("total_amount, created_at") \
        .gte("created_at", f"{now.year}-{now.month:02d}-01") \
        .lt("created_at", f"{now.year}-{now.month+1:02d}-01" if now.month < 12 else f"{now.year+1}-01-01") \
        .execute()
    current_month_total = sum(float(o["total_amount"]) for o in current_month_resp.data or [])

    # Sum revenue for previous month
    prev_year = now.year if now.month > 1 else now.year - 1
    prev_month = now.month - 1 if now.month > 1 else 12
    previous_month_resp = supabase.table("orders") \
        .select("total_amount, created_at") \
        .gte("created_at", f"{prev_year}-{prev_month:02d}-01") \
        .lt("created_at", f"{now.year}-{now.month:02d}-01") \
        .execute()
    previous_month_total = sum(float(o["total_amount"]) for o in previous_month_resp.data or [])

    return {
        "current_month": current_month_total,
        "previous_month": previous_month_total
    }

@router.get("/bookings")
def get_bookings(current_user=Depends(require_admin)):
    # Count bookings with status="CREATED"
    resp = supabase.table("orders") \
        .select("id, status") \
        .eq("status", "CREATED") \
        .execute()
    confirmed_count = len(resp.data or [])
    total_resp = supabase.table("orders") \
        .select("id") \
        .execute()
    total_count = len(total_resp.data or [])
    completion_rate = (confirmed_count / total_count) if total_count else 0.0
    return {
        "confirmed_count": confirmed_count,
        "completion_rate": completion_rate
    }

@router.get("/priests")
def get_priests(current_user=Depends(require_admin)):
    resp = supabase.table("users") \
        .select("id, role, is_active") \
        .eq("role", "priest") \
        .eq("is_active", True) \
        .execute()
    active_priests = len(resp.data or [])
    return {
        "active_priests": active_priests
    }

@router.get("/live_streams")
def get_live_streams(current_user=Depends(require_admin)):
    resp = supabase.table("sessions") \
        .select("id, live_started") \
        .eq("live_started", True) \
        .execute()
    total_views = len(resp.data or [])
    return {
        "total_views": total_views
    }

@router.get("/activity")
def get_activity(current_user=Depends(require_admin)):
    orders_resp = supabase.table("orders") \
        .select("id, status, total_amount, created_at") \
        .order("created_at", desc=True) \
        .limit(5) \
        .execute()
    recent_orders = orders_resp.data or []

    sessions_resp = supabase.table("sessions") \
        .select("id, status, created_at") \
        .order("created_at", desc=True) \
        .limit(5) \
        .execute()
    recent_sessions = sessions_resp.data or []

    users_resp = supabase.table("users") \
        .select("id, email, role, created_at") \
        .order("created_at", desc=True) \
        .limit(5) \
        .execute()
    recent_registrations = users_resp.data or []

    return {
        "recent_orders": recent_orders,
        "recent_sessions": recent_sessions,
        "recent_registrations": recent_registrations
    }
