from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import supabase
from app.schemas.payment import PaymentOut

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)

# --------------------
# Create Payment
# --------------------
@router.post("/", response_model=PaymentOut)
def create_payment_entry(
    order_id: UUID = Query(...),
    method: str = Query(...),
    status: str = Query(...),
    amount: float = Query(...),
    user_id: UUID = Query(...),
):
    # 1. Create payment entry
    payment_resp = (
        supabase
        .table("payments")
        .insert({
            "order_id": str(order_id),
            "method": method,
            "status": status,
            "amount": amount,
        })
        .single()
        .execute()
    )

    if payment_resp.error:
        raise HTTPException(
            status_code=500,
            detail=payment_resp.error.message,
        )

    payment = payment_resp.data

    # 2. Clear cart if payment successful
    if status.upper() == "SUCCESS":
        cart_resp = (
            supabase
            .table("carts")
            .select("id")
            .eq("user_id", str(user_id))
            .single()
            .execute()
        )

        if cart_resp.data:
            cart_id = cart_resp.data["id"]
            supabase.table("cart_items").delete().eq(
                "cart_id", cart_id
            ).execute()

    return payment


# --------------------
# Get Payment by ID
# --------------------
@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: UUID):
    resp = (
        supabase
        .table("payments")
        .select("*")
        .eq("id", str(payment_id))
        .single()
        .execute()
    )

    if not resp.data:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return resp.data


# --------------------
# List Payments by Order
# --------------------
@router.get("/", response_model=List[PaymentOut])
def list_payments(order_id: UUID = Query(...)):
    resp = (
        supabase
        .table("payments")
        .select("*")
        .eq("order_id", str(order_id))
        .execute()
    )

    return resp.data or []