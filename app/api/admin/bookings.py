from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional, Literal
from uuid import uuid4
from datetime import datetime
from app.core.supabase import supabase
from app.services.payment_service import payment_service

router = APIRouter(prefix="/admin/bookings", tags=["Admin Bookings"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AdminBooking(BaseModel):
    id: str
    customer_name: str
    user_id: Optional[str] = None
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    booking_date: Optional[str] = None
    booking_time: Optional[str] = None
    location: Optional[str] = None
    total_amount: float
    admin_net_amount: Optional[float] = None
    created_type: Literal["manual", "razorpay"]
    status: Literal["pending", "completed", "cancelled"]
    created_at: str
    refund_id: Optional[str] = None
    refund_status: Optional[str] = None
    priests: Optional[List[dict]] = None


class CreateBookingRequest(BaseModel):
    customer_name: str
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    booking_date: Optional[str] = None
    booking_time: Optional[str] = None
    location: Optional[str] = None
    total_amount: float
    created_type: Literal["manual", "razorpay"]


class AssignPriestRequest(BaseModel):
    priest_id: str
    commission_percent: float


class AssignPriestsBody(BaseModel):
    priests: List[AssignPriestRequest]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOOKING_SELECT = (
    "id, customer_name, user_id, service_id, service_name, booking_date, "
    "booking_time, location, total_amount, admin_net_amount, status, "
    "created_type, created_at, razorpay_order_id, refund_id, refund_status"
)


def _get_priests_for_booking(booking_id: str) -> list:
    """Fetch assigned priests with resolved names for a given booking."""
    priests_resp = (
        supabase.table("booking_priests")
        .select("id, priest_id, commission_percent, commission_amount")
        .eq("booking_id", booking_id)
        .execute()
    )
    priests = priests_resp.data or []
    if priests:
        priest_ids = [p["priest_id"] for p in priests]
        users_resp = (
            supabase.table("users")
            .select("id, first_name, last_name")
            .in_("id", priest_ids)
            .execute()
        )
        users_map = {
            u["id"]: (
                (u.get("first_name") or "") + " " + (u.get("last_name") or "")
            ).strip()
            for u in users_resp.data or []
        }
        for p in priests:
            p["name"] = users_map.get(p["priest_id"], "Unknown")
    return priests


def _booking_response(booking: dict, priests: list) -> dict:
    """Build a consistent booking response dict."""
    return {
        "id": booking["id"],
        "order_id": booking.get("razorpay_order_id"),
        "customer_id": booking.get("user_id"),
        "customer_name": booking.get("customer_name"),
        "service_id": booking.get("service_id"),
        "service_name": booking.get("service_name"),
        "booking_date": booking.get("booking_date"),
        "booking_time": booking.get("booking_time"),
        "location": booking.get("location"),
        "total_amount": booking.get("total_amount"),
        "admin_net_amount": booking.get("admin_net_amount"),
        "status": booking.get("status"),
        "created_type": booking.get("created_type"),
        "created_at": booking.get("created_at"),
        "refund_id": booking.get("refund_id"),
        "refund_status": booking.get("refund_status"),
        "priests": priests,
    }


# ---------------------------------------------------------------------------
# Routes — specific sub-routes MUST come before the generic /{booking_id}
# ---------------------------------------------------------------------------

@router.get("/")
def list_bookings(current_user=Depends(require_admin)):
    try:
        resp = (
            supabase.table("bookings")
            .select(BOOKING_SELECT)
            .order("created_at", desc=True)
            .execute()
        )
        bookings = resp.data or []
        return [
            _booking_response(booking, _get_priests_for_booking(booking["id"]))
            for booking in bookings
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/", status_code=201)
def create_booking(booking: CreateBookingRequest, current_user=Depends(require_admin)):
    if not (booking.service_id or booking.service_name):
        raise HTTPException(
            status_code=422,
            detail="At least one of service_id or service_name is required.",
        )
    try:
        booking_id = str(uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        insert_data = {
            "id": booking_id,
            "customer_name": booking.customer_name,
            "service_id": booking.service_id,
            "service_name": booking.service_name,
            "booking_date": booking.booking_date,
            "booking_time": booking.booking_time,
            "location": booking.location,
            "total_amount": booking.total_amount,
            "created_type": booking.created_type,
            "status": "pending",
            "created_at": created_at,
        }
        resp = supabase.table("bookings").insert(insert_data).execute()
        row = resp.data[0] if resp.data else insert_data
        return row
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{booking_id}/cancel")
def cancel_booking(booking_id: str, current_user=Depends(require_admin)):
    """
    Cancel a booking.
    - For razorpay bookings, initiates a full Razorpay refund automatically.
    - Updates refund_id and refund_status in both bookings and payments tables.
    """
    booking_resp = (
        supabase.table("bookings")
        .select(BOOKING_SELECT)
        .eq("id", booking_id)
        .single()
        .execute()
    )
    if not booking_resp.data:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = booking_resp.data

    if booking.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled")

    refund_id = None
    refund_status = None

    # ── Razorpay refund ────────────────────────────────────────────────────
    if booking.get("created_type") == "razorpay" and booking.get("razorpay_order_id"):
        try:
            payment_resp = (
                supabase.table("payments")
                .select("id, razorpay_payment_id, amount")
                .eq("razorpay_order_id", booking["razorpay_order_id"])
                .single()
                .execute()
            )

            if payment_resp.data and payment_resp.data.get("razorpay_payment_id"):
                razorpay_payment_id = payment_resp.data["razorpay_payment_id"]
                amount_paise = int(float(booking["total_amount"]) * 100)

                refund_result = payment_service.refund_payment(
                    razorpay_payment_id, amount_paise
                )
                refund_id = refund_result.get("id")
                refund_status = refund_result.get("status", "initiated")

                # Also update payments table
                supabase.table("payments").update(
                    {"refund_id": refund_id, "refund_status": refund_status}
                ).eq("razorpay_order_id", booking["razorpay_order_id"]).execute()
            else:
                refund_status = "no_payment_found"
        except Exception as refund_exc:
            # Log but don't block the cancellation if refund fails
            print(f"[WARN] Refund failed for booking {booking_id}: {refund_exc}")
            refund_status = "failed"

    # ── Update booking ─────────────────────────────────────────────────────
    update_data: dict = {"status": "cancelled"}
    if refund_id:
        update_data["refund_id"] = refund_id
    if refund_status:
        update_data["refund_status"] = refund_status

    update_resp = (
        supabase.table("bookings").update(update_data).eq("id", booking_id).execute()
    )
    if not update_resp.data:
        raise HTTPException(status_code=404, detail="Booking not found")

    updated_booking = update_resp.data[0]
    priests = _get_priests_for_booking(booking_id)
    return _booking_response(updated_booking, priests)


@router.put("/{booking_id}/complete")
def complete_booking(booking_id: str, current_user=Depends(require_admin)):
    """Mark a booking as completed manually (without assigning priests)."""
    booking_resp = (
        supabase.table("bookings")
        .select(BOOKING_SELECT)
        .eq("id", booking_id)
        .single()
        .execute()
    )
    if not booking_resp.data:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking_resp.data.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Booking is already completed")

    update_resp = (
        supabase.table("bookings")
        .update({"status": "completed"})
        .eq("id", booking_id)
        .execute()
    )
    if not update_resp.data:
        raise HTTPException(status_code=404, detail="Booking not found")

    updated_booking = update_resp.data[0]
    priests = _get_priests_for_booking(booking_id)
    return _booking_response(updated_booking, priests)


@router.post("/{booking_id}/assign-priests")
def assign_priests(
    booking_id: str, body: AssignPriestsBody, current_user=Depends(require_admin)
):
    """
    Assign (or re-assign) priests to a booking.
    - Deletes existing assignments first so re-calling is safe (idempotent).
    - Commission is calculated sequentially from total_amount.
    - Sets booking status to 'completed' and updates admin_net_amount.
    """
    booking_resp = (
        supabase.table("bookings")
        .select(BOOKING_SELECT)
        .eq("id", booking_id)
        .single()
        .execute()
    )
    if not booking_resp.data:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = booking_resp.data

    # Snapshot existing priests so we can restore on failure
    existing_priests_resp = (
        supabase.table("booking_priests")
        .select("*")
        .eq("booking_id", booking_id)
        .execute()
    )
    existing_priests_snapshot = existing_priests_resp.data or []

    try:
        # Remove existing priest assignments (allows safe re-assignment)
        supabase.table("booking_priests").delete().eq("booking_id", booking_id).execute()

        total_amount = float(booking["total_amount"])
        commission_rows = []
        total_commissions = 0.0

        for priest in body.priests:
            commission_amount = round(
                (total_amount * priest.commission_percent) / 100.0, 2
            )
            total_commissions += commission_amount
            insert_resp = (
                supabase.table("booking_priests")
                .insert(
                    {
                        "booking_id": booking_id,
                        "priest_id": priest.priest_id,
                        "commission_percent": priest.commission_percent,
                        "commission_amount": commission_amount,
                    }
                )
                .execute()
            )
            if not insert_resp.data:
                raise HTTPException(
                    status_code=500, detail="Failed to insert booking_priest record"
                )
            commission_rows.append(
                {
                    "id": insert_resp.data[0]["id"],
                    "priest_id": priest.priest_id,
                    "commission_percent": priest.commission_percent,
                    "commission_amount": commission_amount,
                }
            )

        admin_net_amount = round(total_amount - total_commissions, 2)

        update_resp = (
            supabase.table("bookings")
            .update({"admin_net_amount": admin_net_amount, "status": "completed"})
            .eq("id", booking_id)
            .execute()
        )
        updated_booking = update_resp.data[0] if update_resp.data else booking
        updated_booking["admin_net_amount"] = admin_net_amount
        updated_booking["status"] = "completed"

        # Resolve priest names
        priest_ids = [p["priest_id"] for p in commission_rows]
        users_resp = (
            supabase.table("users")
            .select("id, first_name, last_name")
            .in_("id", priest_ids)
            .execute()
        )
        users_map = {
            u["id"]: (
                (u.get("first_name") or "") + " " + (u.get("last_name") or "")
            ).strip()
            for u in users_resp.data or []
        }
        priests_out = [
            {
                "id": p["id"],
                "priest_id": p["priest_id"],
                "name": users_map.get(p["priest_id"], "Unknown"),
                "commission_percent": p["commission_percent"],
                "commission_amount": p["commission_amount"],
            }
            for p in commission_rows
        ]

        return _booking_response(updated_booking, priests_out)

    except HTTPException:
        # Restore previous priests if something went wrong mid-flight
        if existing_priests_snapshot:
            for row in existing_priests_snapshot:
                row.pop("id", None)  # let DB generate a new id
                supabase.table("booking_priests").insert(row).execute()
        raise
    except Exception as exc:
        # Restore previous priests on unexpected error
        if existing_priests_snapshot:
            for row in existing_priests_snapshot:
                row.pop("id", None)
                supabase.table("booking_priests").insert(row).execute()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{booking_id}")
def get_booking(booking_id: str, current_user=Depends(require_admin)):
    try:
        resp = (
            supabase.table("bookings")
            .select(BOOKING_SELECT)
            .eq("id", booking_id)
            .single()
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        priests = _get_priests_for_booking(booking_id)
        return _booking_response(resp.data, priests)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{booking_id}")
def update_booking(
    booking_id: str, booking: AdminBooking, current_user=Depends(require_admin)
):
    try:
        resp = (
            supabase.table("bookings")
            .update(booking.dict(exclude_none=True))
            .eq("id", booking_id)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Booking not found")
        return resp.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{booking_id}", status_code=204)
def delete_booking(booking_id: str, current_user=Depends(require_admin)):
    try:
        supabase.table("bookings").delete().eq("id", booking_id).execute()
        return None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
