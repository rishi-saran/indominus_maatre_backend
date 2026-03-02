from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import require_admin
from app.core.supabase import supabase
from datetime import datetime

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])

# Change route to match /api/v1/admin/reports/summary
@router.get("/summary")
def get_reports_summary(
    year: int = Query(None, description="Year to filter bookings and revenue (default: current year)"),
    months: str = Query(None, description="Comma-separated months to filter (e.g. '1,2,3')"),
    current_user=Depends(require_admin)
):
    now = datetime.utcnow()
    year = year or now.year
    # Parse months if provided, else use last 6 months
    if months:
        month_list = [int(m) for m in months.split(",") if m.isdigit() and 1 <= int(m) <= 12]
    else:
        month_list = [(now.month - i - 1) % 12 + 1 for i in reversed(range(6))]
    month_list = sorted(set(month_list))

    # Revenue Growth (from orders with status 'created')
    monthly_revenue = []
    total_revenue = 0
    for m in month_list:
        start = datetime(year, m, 1)
        if m == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, m + 1, 1)
        orders_resp = supabase.table("orders").select("total_amount, status, created_at").gte("created_at", start.isoformat()).lt("created_at", end.isoformat()).execute()
        month_sum = 0.0
        for o in (orders_resp.data or []):
            status = o.get("status", "").lower()
            amt = o.get("total_amount")
            if status in ["created", "created"] and amt is not None:
                try:
                    month_sum += float(amt)
                except (ValueError, TypeError):
                    continue
        monthly_revenue.append({"month": start.strftime("%b"), "year": year, "revenue": month_sum})
        total_revenue += month_sum

    # All-time total revenue (status 'created')
    all_orders_resp = supabase.table("orders").select("total_amount, status").execute()
    all_revenue = 0.0
    for o in (all_orders_resp.data or []):
        status = o.get("status", "").lower()
        amt = o.get("total_amount")
        if status in ["created", "created"] and amt is not None:
            try:
                all_revenue += float(amt)
            except (ValueError, TypeError):
                continue
    avg_monthly = all_revenue / 12 if all_revenue else 0
    # Revenue growth %
    growth_percent = 0
    if len(monthly_revenue) >= 2 and monthly_revenue[-2]["revenue"]:
        growth_percent = round(100 * (monthly_revenue[-1]["revenue"] - monthly_revenue[-2]["revenue"]) / monthly_revenue[-2]["revenue"])

    # User Demographics
    users_resp = supabase.table("users").select("id, role, created_at").execute()
    users = users_resp.data or []
    total_users = len(users)
    customers = [u for u in users if u.get("role") == "customer"]
    priests = [u for u in users if u.get("role") == "priest"]
    num_customers = len(customers)
    num_priests = len(priests)
    customer_percent = round(100 * num_customers / total_users, 1) if total_users else 0
    priest_percent = round(100 * num_priests / total_users, 1) if total_users else 0
    # New users this month
    this_month = now.strftime("%Y-%m")
    new_this_month = len([u for u in users if u.get("created_at", "").startswith(this_month)])

    # Monthly Booking Trends
    bookings = []
    for m in month_list:
        start = datetime(year, m, 1)
        if m == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, m + 1, 1)
        orders = supabase.table("orders").select("status, created_at").gte("created_at", start.isoformat()).lt("created_at", end.isoformat()).execute()
        confirmed = len([o for o in (orders.data or []) if o.get("status", "").lower() == "confirmed"])
        cancelled = len([o for o in (orders.data or []) if o.get("status", "").lower() == "cancelled"])
        bookings.append({"month": start.strftime("%b"), "year": year, "confirmed": confirmed, "cancelled": cancelled})

    return {
        "revenue": {
            "monthly": monthly_revenue,
            "total": all_revenue,
            "averageMonthly": avg_monthly,
            "growthPercent": growth_percent
        },
        "users": {
            "total": total_users,
            "customers": num_customers,
            "priests": num_priests,
            "customerPercent": customer_percent,
            "priestPercent": priest_percent,
            "newThisMonth": new_this_month
        },
        "bookings": bookings
    }