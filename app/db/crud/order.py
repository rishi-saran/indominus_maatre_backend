from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.cart import Cart
from app.models.service import Service
from app.models.service_package import ServicePackage
from app.models.service_addon import ServiceAddon


# --------------------
# Create Order from Cart
# --------------------
async def create_order_from_cart(
    db: AsyncSession,
    user_id: UUID,
    provider_id: UUID | None,
    address_id: UUID | None,
) -> Order:
    # Fetch cart with items
    stmt = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items))
    )
    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()

    if not cart or not cart.items:
        raise ValueError("Cart is empty")

    total_amount = 0.0
    order_items: List[OrderItem] = []

    # Calculate pricing
    for item in cart.items:
        price = 0.0

        if item.package_id:
            pkg = await db.get(ServicePackage, item.package_id)
            price += float(pkg.price)

        if item.addon_id:
            addon = await db.get(ServiceAddon, item.addon_id)
            price += float(addon.price)

        if not item.package_id and not item.addon_id:
            service = await db.get(Service, item.service_id)
            price += float(service.base_price or 0)

        price *= item.quantity
        total_amount += price

        order_items.append(
            OrderItem(
                service_id=item.service_id,
                package_id=item.package_id,
                addon_id=item.addon_id,
                price=price,
            )
        )

    # Create order
    order = Order(
        user_id=user_id,
        provider_id=provider_id,
        address_id=address_id,
        total_amount=total_amount,
        status="PENDING",
        items=order_items,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


# --------------------
# Get Order by ID
# --------------------
async def get_order_by_id(
    db: AsyncSession,
    order_id: UUID,
) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# --------------------
# List Orders by User
# --------------------
async def get_orders_by_user(
    db: AsyncSession,
    user_id: UUID,
) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
    )
    result = await db.execute(stmt)
    return result.scalars().all()