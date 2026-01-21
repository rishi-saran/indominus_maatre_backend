from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel


class PaymentOut(BaseModel):
    id: UUID
    order_id: UUID

    method: Optional[str] = None
    status: str
    amount: float

    currency: Optional[str] = "INR"

    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

    refund_id: Optional[str] = None
    failure_reason: Optional[str] = None

    class Config:
        from_attributes = True


# --------------------
# Razorpay Order Creation
# --------------------
class CreateOrderRequest(BaseModel):
    amount: float  # Amount in INR (e.g., 100 for 100 INR, 100.50 for 100.50 INR)
    currency: str = "INR"
    order_id: Optional[str] = None
    user_email: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None


class CreateOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int  # Amount in paise
    currency: str


# --------------------
# Razorpay Payment Verification
# --------------------
class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_id: Optional[str] = None


class VerifyPaymentResponse(BaseModel):
    success: bool
    payment_id: str
    message: Optional[str] = None