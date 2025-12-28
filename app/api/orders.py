from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.order import (
    create_order_from_cart,
    get_order_by_id,
    get_orders_by_user,
)
from app.schemas.order import OrderOut

router = APIRouter(
    tags=["Orders"]
)


# --------------------
# Create Order from Cart
# --------------------
@router.post("/", response_model=OrderOut)
async def create_order(
    user_id: UUID = Query(...),
    provider_id: Optional[UUID] = Query(None),
    address_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_order_from_cart(
            db=db,
            user_id=user_id,
            provider_id=provider_id,
            address_id=address_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --------------------
# Get Order by ID
# --------------------
@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    order = await get_order_by_id(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


# --------------------
# List Orders by User
# --------------------
@router.get("/", response_model=List[OrderOut])
async def list_orders(
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await get_orders_by_user(db, user_id)