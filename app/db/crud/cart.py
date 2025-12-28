from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem


# --------------------
# Get or Create Cart
# --------------------
async def get_or_create_cart(
    db: AsyncSession,
    user_id: UUID,
) -> Cart:
    stmt = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items))
    )

    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()

    if cart:
        return cart

    cart = Cart(user_id=user_id)
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return cart


# --------------------
# Get Cart with Items
# --------------------
async def get_cart(
    db: AsyncSession,
    user_id: UUID,
) -> Cart | None:
    stmt = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items))
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# --------------------
# Add Item to Cart
# --------------------
async def add_cart_item(
    db: AsyncSession,
    cart_id: UUID,
    service_id: UUID,
    package_id: UUID | None,
    addon_id: UUID | None,
    quantity: int = 1,
) -> CartItem:
    item = CartItem(
        cart_id=cart_id,
        service_id=service_id,
        package_id=package_id,
        addon_id=addon_id,
        quantity=quantity,
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


# --------------------
# Remove Item from Cart
# --------------------
async def remove_cart_item(
    db: AsyncSession,
    item_id: UUID,
) -> None:
    stmt = delete(CartItem).where(CartItem.id == item_id)
    await db.execute(stmt)
    await db.commit()

# --------------------
# Clear Cart Items
# --------------------
async def clear_cart(
    db,
    cart_id: UUID,
) -> None:
    stmt = delete(CartItem).where(CartItem.cart_id == cart_id)
    await db.execute(stmt)
    await db.commit()