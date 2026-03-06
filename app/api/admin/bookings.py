from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.core.supabase import get_service_role_client
from app.services.payment_service import payment_service


class PriestAssignment(BaseModel):
    priest_id: UUID
    commission_percent: float


class BookingPriest(BaseModel):
    priest_id: UUID
    commission_percent: float
    commission_amount: float


class AssignPriestsRequest(BaseModel):
    priests: List[PriestAssignment]


class RefundRequest(BaseModel):
    razorpay_payment_id: str
    amount: Optional[int] = None  # paise


class AdminBooking(BaseModel):
    id: Optional[UUID] = None
    customer_name: Optional[str] = None
    user_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    service_name: Optional[str] = None
    booking_date: Optional[str] = None
    booking_time: Optional[str] = None
    location: Optional[str] = None
    total_amount: Optional[float] = None
    admin_net_amount: Optional[float] = None
    status: Optional[str] = None
    created_type: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    refund_id: Optional[str] = None
    refund_status: Optional[str] = None
    created_at: Optional[str] = None
    priests: Optional[List[BookingPriest]] = None


class AdminBookingCreate(BaseModel):
    customer_name: str
    service_id: UUID
    service_name: str
    booking_date: str
    booking_time: str
    location: str
    total_amount: float
    created_type: str
    user_id: Optional[UUID] = None
    razorpay_order_id: Optional[str] = None


router = APIRouter(prefix="/admin/bookings", tags=["Admin Bookings"])


@router.get("/", response_model=List[AdminBooking])
def list_bookings(current_user=Depends(require_admin)):
    client = get_service_role_client()
    resp = client.table("bookings").select("*").execute()
    bookings = resp.data or []
    # populate priests list for each booking so frontend can safely map
    for booking in bookings:
        pri_resp = client.table("booking_priests")
        pri_resp = pri_resp.select("priest_id,commission_percent,commission_amount")
        pri_resp = pri_resp.eq("booking_id", booking.get("id")).execute()
        booking["priests"] = pri_resp.data or []
    return bookings


@router.get("/{booking_id}", response_model=AdminBooking)
def get_booking(booking_id: str, current_user=Depends(require_admin)):
    client = get_service_role_client()
    resp = client.table("bookings").select("*").eq("id", booking_id).limit(1).execute()
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking = rows[0]
    # fetch assigned priests for this booking
    pri_resp = client.table("booking_priests")
    pri_resp = pri_resp.select("priest_id,commission_percent,commission_amount")
    pri_resp = pri_resp.eq("booking_id", booking_id).execute()
    booking["priests"] = pri_resp.data or []
    return booking


@router.post("/", response_model=AdminBooking, status_code=status.HTTP_201_CREATED)
def create_booking(booking: AdminBookingCreate, current_user=Depends(require_admin)):
    client = get_service_role_client()
    # mode="json" converts UUID/datetime objects to strings automatically
    payload = booking.model_dump(mode="json")
    # starting net amount equals total until priests assigned
    payload["admin_net_amount"] = payload.get("total_amount")
    payload["status"] = "pending"
    resp = client.table("bookings").insert(payload).execute()
    created = resp.data or []
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create booking")
    return created[0]


@router.put("/{booking_id}", response_model=AdminBooking)
def update_booking(booking_id: str, booking: AdminBookingCreate, current_user=Depends(require_admin)):
    client = get_service_role_client()
    update_data = booking.model_dump(mode="json", exclude_none=True)
    resp = client.table("bookings").update(update_data).eq("id", booking_id).execute()
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")
    return rows[0]


@router.post("/{booking_id}/assign-priests", response_model=AdminBooking)
def assign_priests(booking_id: str, payload: AssignPriestsRequest, current_user=Depends(require_admin)):
    client = get_service_role_client()
    # ensure booking exists and fetch total_amount
    bk_resp = client.table("bookings").select("total_amount").eq("id", booking_id).limit(1).execute()
    rows = bk_resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")
    total = rows[0].get("total_amount") or 0

    # remove previous assignments
    client.table("booking_priests").delete().eq("booking_id", booking_id).execute()

    # calculate commissions sequentially
    remaining = total
    new_rows = []
    for p in payload.priests:
        commission_amt = remaining * (p.commission_percent / 100)
        new_rows.append({
            "booking_id": booking_id,
            "priest_id": str(p.priest_id),
            "commission_percent": p.commission_percent,
            "commission_amount": commission_amt,
        })
        remaining -= commission_amt
    if new_rows:
        client.table("booking_priests").insert(new_rows).execute()

    # update booking net amount and status
    client.table("bookings").update({
        "admin_net_amount": remaining,
        "status": "completed",
    }).eq("id", booking_id).execute()

    # return fresh booking with priests
    return get_booking(booking_id, current_user)


@router.post("/{booking_id}/refund")
def refund_booking(booking_id: str, request: RefundRequest, current_user=Depends(require_admin)):
    client = get_service_role_client()
    resp = client.table("bookings").select("*").eq("id", booking_id).limit(1).execute()
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking = rows[0]
    try:
        refund_resp = payment_service.refund_payment(request.razorpay_payment_id, request.amount)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    client.table("bookings").update({
        "refund_id": refund_resp.get("id"),
        "refund_status": refund_resp.get("status"),
        "status": "cancelled",
    }).eq("id", booking_id).execute()
    return {"booking": booking, "refund": refund_resp}


@router.api_route("/{booking_id}/cancel", methods=["POST", "PUT"])
def cancel_booking(booking_id: str, current_user=Depends(require_admin)):
    """Cancel a booking. For Razorpay bookings, initiates a refund automatically.
    For manual bookings, just marks as cancelled with refund_status='manual_refund_pending'."""
    client = get_service_role_client()
    resp = client.table("bookings").select("*").eq("id", booking_id).limit(1).execute()
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking = rows[0]

    if booking.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled")

    created_type = booking.get("created_type", "manual")
    razorpay_order_id = booking.get("razorpay_order_id")
    refund_result = None

    if created_type == "razorpay" and razorpay_order_id:
        # fetch the payment ID from Razorpay order
        try:
            payments = payment_service.client.order.payments(razorpay_order_id)
            payment_items = payments.get("items", [])
            if payment_items:
                razorpay_payment_id = payment_items[0]["id"]
                refund_result = payment_service.refund_payment(razorpay_payment_id)
                client.table("bookings").update({
                    "refund_id": refund_result.get("id"),
                    "refund_status": refund_result.get("status"),
                    "status": "cancelled",
                }).eq("id", booking_id).execute()
            else:
                # no payment found, just cancel
                client.table("bookings").update({
                    "status": "cancelled",
                    "refund_status": "no_payment_found",
                }).eq("id", booking_id).execute()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Refund failed: {str(exc)}")
    else:
        # manual booking — no Razorpay payment, just cancel
        client.table("bookings").update({
            "status": "cancelled",
            "refund_status": "manual_refund_pending",
        }).eq("id", booking_id).execute()

    updated = client.table("bookings").select("*").eq("id", booking_id).limit(1).execute()
    return {
        "booking": updated.data[0],
        "refund": refund_result,
        "message": "Booking cancelled successfully. Refund initiated." if refund_result else "Booking cancelled.",
    }


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: str, current_user=Depends(require_admin)):
    client = get_service_role_client()
    resp = client.table("bookings").delete().eq("id", booking_id).execute()
    if resp.count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return None
