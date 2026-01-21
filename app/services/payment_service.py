import hmac
import hashlib
from typing import Dict, Any, Optional
from uuid import UUID

import razorpay

from app.core.config import settings


class RazorpayService:
    """Service to handle Razorpay payment gateway operations"""

    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        order_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order for payment

        Args:
            amount: Amount in paise (smallest unit, so 1000 = 10 INR)
            currency: Currency code (default: INR)
            order_id: Business order ID
            user_email: Customer email
            notes: Additional notes/metadata for the order

        Returns:
            Dictionary containing razorpay_order_id, amount, and currency
        """
        try:
            # Prepare notes
            order_notes = notes or {}
            if order_id:
                order_notes["order_id"] = str(order_id)
            if user_email:
                order_notes["user_email"] = user_email

            # Create order via Razorpay
            response = self.client.order.create(
                {
                    "amount": amount,  # Amount in paise
                    "currency": currency,
                    "notes": order_notes,
                }
            )

            return {
                "razorpay_order_id": response["id"],
                "amount": amount,
                "currency": currency,
            }
        except Exception as e:
            raise Exception(f"Failed to create Razorpay order: {str(e)}")

    def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verify Razorpay payment signature

        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Signature from Razorpay response

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Create the message that needs to be signed
            message = f"{razorpay_order_id}|{razorpay_payment_id}"

            # Create HMAC SHA256 signature using KEY_SECRET (not webhook secret)
            generated_signature = hmac.new(
                self.key_secret.encode(),
                message.encode(),
                hashlib.sha256,
            ).hexdigest()

            # Compare signatures
            return generated_signature == razorpay_signature
        except Exception as e:
            print(f"Signature verification error: {str(e)}")
            raise Exception(f"Failed to verify payment: {str(e)}")

    def fetch_payment(self, razorpay_payment_id: str) -> Dict[str, Any]:
        """
        Fetch payment details from Razorpay

        Args:
            razorpay_payment_id: Razorpay payment ID

        Returns:
            Payment details dictionary
        """
        try:
            return self.client.payment.fetch(razorpay_payment_id)
        except Exception as e:
            raise Exception(f"Failed to fetch payment: {str(e)}")

    def refund_payment(
        self, razorpay_payment_id: str, amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Refund a payment

        Args:
            razorpay_payment_id: Razorpay payment ID
            amount: Amount to refund in paise (None = full refund)

        Returns:
            Refund details dictionary
        """
        try:
            refund_data = {}
            if amount:
                refund_data["amount"] = amount

            return self.client.payment.refund(razorpay_payment_id, refund_data)
        except Exception as e:
            raise Exception(f"Failed to refund payment: {str(e)}")


# Initialize service
payment_service = RazorpayService()
