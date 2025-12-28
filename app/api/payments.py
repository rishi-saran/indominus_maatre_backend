from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.payment import (
    create_payment,
    get_payment_by_id,
    get_payments_by_order,
)
from app.schemas.payment import PaymentOut

router = APIRouter(
    tags=["Payments"]
)


# --------------------
# Create Payment
# --------------------
@router.post("/", response_model=PaymentOut)
async def create_payment_entry(
    order_id: UUID = Query(...),
    method: str = Query(...),
    status: str = Query(...),
    amount: float = Query(...),
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    payment = await create_payment(
        db=db,
        order_id=order_id,
        method=method,
        status=status,
        amount=amount,
    )

    # --------------------
    # Clear cart on success
    # --------------------
    if status.upper() == "SUCCESS":
        from app.db.crud.cart import get_cart, clear_cart

        cart = await get_cart(db, user_id)
        if cart:
            await clear_cart(db, cart.id)

    return payment

# --------------------
# Get Payment by ID
# --------------------
@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    payment = await get_payment_by_id(db, payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment


# --------------------
# List Payments by Order
# --------------------
@router.get("/", response_model=List[PaymentOut])
async def list_payments(
    order_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await get_payments_by_order(db, order_id)