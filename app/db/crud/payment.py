from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


# --------------------
# Create Payment
# --------------------
async def create_payment(
    db: AsyncSession,
    order_id: UUID,
    method: str,
    status: str,
    amount: float,
) -> Payment:
    payment = Payment(
        order_id=order_id,
        method=method,
        status=status,
        amount=amount,
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


# --------------------
# Get Payment by ID
# --------------------
async def get_payment_by_id(
    db: AsyncSession,
    payment_id: UUID,
) -> Payment | None:
    stmt = select(Payment).where(Payment.id == payment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# --------------------
# List Payments by Order
# --------------------
async def get_payments_by_order(
    db: AsyncSession,
    order_id: UUID,
) -> List[Payment]:
    stmt = select(Payment).where(Payment.order_id == order_id)
    result = await db.execute(stmt)
    return result.scalars().all()