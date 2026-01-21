from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user
from app.schemas.payment import (
    PaymentOut,
    CreateOrderRequest,
    CreateOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


# --------------------
# Helpers
# --------------------
def _normalize_amount_to_paise(amount: float) -> int:
    """Accept amount in INR or paise and return paise.

    - If amount <= 0 -> raise
    - If amount > 100_000 -> we assume caller sent paise (e.g., 1179900 for ₹11,799)
    - After normalization, enforce the 1 lakh INR cap (10_000_000 paise)
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    # Heuristic: if amount is huge, treat it as already in paise
    if amount > 100_000:
        amount_in_paise = int(amount)
    else:
        amount_in_paise = int(amount * 100)

    # Enforce max: 1 lakh INR => 10,000,000 paise
    if amount_in_paise > 10_000_000:
        raise HTTPException(status_code=400, detail="Amount exceeds maximum limit of 1,00,000 INR. For amounts above 1 lakh, please split into multiple payments.")

    return amount_in_paise


# --------------------
# Health Check (for testing without auth)
# --------------------
@router.get("/health")
def payment_health():
    """
    Test endpoint to verify Razorpay service is operational
    """
    return {"status": "ok", "message": "Payment service is running"}


# --------------------
# Create Razorpay Order (TEST - No Auth Required)
# --------------------
@router.post("/create-order-test", response_model=CreateOrderResponse)
def create_razorpay_order_test(
    request: CreateOrderRequest,
):
    """
    TEST endpoint - Create a Razorpay order WITHOUT authentication
    Use this to debug request format issues
    """
    try:
        print(f"Received create-order-test request: amount={request.amount}, currency={request.currency}")
        
        # Normalize amount: accept INR or paise, enforce max
        amount_in_paise = _normalize_amount_to_paise(request.amount)

        # Create order via Razorpay
        response = payment_service.create_order(
            amount=amount_in_paise,
            currency=request.currency,
            order_id=request.order_id,
            user_email=request.user_email or "test@example.com",
            notes=request.notes,
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating Razorpay order: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


# --------------------
# Create Razorpay Order
# --------------------
@router.post("/create-order", response_model=CreateOrderResponse)
def create_razorpay_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a Razorpay order for payment initiation

    - Accept: { amount: number (in INR), currency: "INR", notes: { order_id: string, user_email: string } }
    - Use Razorpay library to create order: razorpay.orders.create()
    - Return: { razorpay_order_id: string, amount: number (in paise), currency: string }
    """
    try:
        print(f"Received create-order request: amount={request.amount}, currency={request.currency}")
        
        # Normalize amount: accept INR or paise, enforce max
        amount_in_paise = _normalize_amount_to_paise(request.amount)

        # Prepare notes with user email
        notes = request.notes or {}
        notes["user_email"] = current_user.get("email", request.user_email or "")

        # Create order via Razorpay
        response = payment_service.create_order(
            amount=amount_in_paise,
            currency=request.currency,
            order_id=request.order_id,
            user_email=current_user.get("email", request.user_email),
            notes=notes,
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating Razorpay order: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


# --------------------
# Verify Razorpay Payment
# --------------------
@router.post("/verify", response_model=VerifyPaymentResponse)
def verify_razorpay_payment(
    request: VerifyPaymentRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Verify Razorpay payment signature and update order status

    - Accept: { razorpay_order_id: string, razorpay_payment_id: string, razorpay_signature: string, order_id: string }
    - Verify signature using Razorpay library
    - Update order status to "paid" in database
    - Return: { success: true, payment_id: string }
    """
    try:
        # Verify payment signature
        is_valid = payment_service.verify_payment(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature,
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        # Fetch payment details from Razorpay
        payment_details = payment_service.fetch_payment(request.razorpay_payment_id)

        # If order_id provided, update the order status in database
        if request.order_id:
            user_id = current_user["id"]

            # Verify order belongs to current user
            order_resp = (
                supabase
                .table("orders")
                .select("id")
                .eq("id", str(request.order_id))
                .eq("user_id", str(user_id))
                .single()
                .execute()
            )

            if not order_resp.data:
                raise HTTPException(status_code=404, detail="Order not found")

            # Create/Update payment record in database
            payment_resp = (
                supabase
                .table("payments")
                .insert({
                    "order_id": str(request.order_id),
                    "method": "razorpay",
                    "status": "PAID" if payment_details.get("status") == "captured" else "PENDING",
                    "amount": payment_details.get("amount", 0) / 100,  # Convert from paise
                    "currency": payment_details.get("currency", "INR"),
                    "razorpay_order_id": request.razorpay_order_id,
                    "razorpay_payment_id": request.razorpay_payment_id,
                    "razorpay_signature": request.razorpay_signature,
                })
                .single()
                .execute()
            )

            if payment_resp.error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save payment: {payment_resp.error.message}",
                )

            # Update order status to PAID
            order_update = (
                supabase
                .table("orders")
                .update({"status": "PAID"})
                .eq("id", str(request.order_id))
                .execute()
            )

            if order_update.error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update order: {order_update.error.message}",
                )

        return VerifyPaymentResponse(
            success=True,
            payment_id=request.razorpay_payment_id,
            message="Payment verified and order updated successfully",
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error verifying payment: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to verify payment: {str(e)}")



@router.post("/", response_model=PaymentOut)
def create_payment_entry(
    order_id: UUID = Query(...),
    method: str = Query(...),
    status: str = Query(...),
    amount: float = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """
    This endpoint records a payment for an existing order.
    - User must own the order
    - Used after payment gateway confirmation
    """
    user_id: UUID = current_user["id"]

    # 1. Verify order belongs to user
    order_resp = (
        supabase
        .table("orders")
        .select("id")
        .eq("id", str(order_id))
        .eq("user_id", str(user_id))
        .single()
        .execute()
    )

    if not order_resp.data:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2. Create payment record
    payment_resp = (
        supabase
        .table("payments")
        .insert({
            "order_id": str(order_id),
            "method": method,
            "status": status.upper(),
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

    # 3. If payment successful → update order status
    if status.upper() == "SUCCESS":
        supabase.table("orders").update(
            {"status": "PAID"}
        ).eq(
            "id", str(order_id)
        ).execute()

    return payment


# --------------------
# Get Payment by ID (Owner only)
# --------------------
@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    resp = (
        supabase
        .table("payments")
        .select("*, orders!inner(user_id)")
        .eq("id", str(payment_id))
        .eq("orders.user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="Payment not found")

    return resp.data[0]


# --------------------
# List Payments by Order (Owner only)
# --------------------
@router.get("/", response_model=List[PaymentOut])
def list_payments(
    order_id: UUID = Query(...),
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    resp = (
        supabase
        .table("payments")
        .select("*, orders!inner(user_id)")
        .eq("order_id", str(order_id))
        .eq("orders.user_id", str(user_id))
        .execute()
    )

    return resp.data or []