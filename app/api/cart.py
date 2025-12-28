from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.crud.cart import (
    get_or_create_cart,
    get_cart,
    add_cart_item,
    remove_cart_item,
)
from app.schemas.cart import CartOut
from app.schemas.cart_item import CartItemOut

router = APIRouter(
    tags=["Cart"]
)


# --------------------
# Get or Create Cart
# --------------------
@router.post("/", response_model=CartOut)
async def create_or_get_cart(
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await get_or_create_cart(db, user_id)


# --------------------
# Get Cart
# --------------------
@router.get("/", response_model=CartOut)
async def get_user_cart(
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_cart(db, user_id)

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return cart


# --------------------
# Add Item to Cart
# --------------------
@router.post("/items", response_model=CartItemOut)
async def add_item_to_cart(
    cart_id: UUID = Query(...),
    service_id: UUID = Query(...),
    package_id: UUID | None = Query(None),
    addon_id: UUID | None = Query(None),
    quantity: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    return await add_cart_item(
        db=db,
        cart_id=cart_id,
        service_id=service_id,
        package_id=package_id,
        addon_id=addon_id,
        quantity=quantity,
    )


# --------------------
# Remove Item from Cart
# --------------------
@router.delete("/items/{item_id}")
async def remove_item_from_cart(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await remove_cart_item(db, item_id)
    return {"status": "item removed"}