from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import supabase
from app.schemas.order import OrderOut

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)

# --------------------
# Create Order from Cart
# --------------------
@router.post("/", response_model=OrderOut)
def create_order(
    user_id: UUID = Query(...),
    provider_id: Optional[UUID] = Query(None),
    address_id: Optional[UUID] = Query(None),
):
    # 1. Fetch user's cart
    cart_resp = (
        supabase
        .table("carts")
        .select("id, cart_items(*)")
        .eq("user_id", str(user_id))
        .single()
        .execute()
    )

    if not cart_resp.data or not cart_resp.data.get("cart_items"):
        raise HTTPException(
            status_code=400,
            detail="Cart is empty or not found",
        )

    cart = cart_resp.data
    cart_items = cart["cart_items"]

    # 2. Calculate total amount
    total_amount = 0
    for item in cart_items:
        total_amount += float(item.get("quantity", 1))

    # 3. Create order
    order_payload = {
        "user_id": str(user_id),
        "provider_id": str(provider_id) if provider_id else None,
        "address_id": str(address_id) if address_id else None,
        "total_amount": total_amount,
        "status": "created",
    }

    order_resp = (
        supabase
        .table("orders")
        .insert(order_payload)
        .single()
        .execute()
    )

    if order_resp.error:
        raise HTTPException(
            status_code=500,
            detail=order_resp.error.message,
        )

    order = order_resp.data

    # 4. Insert order items
    for item in cart_items:
        supabase.table("order_items").insert({
            "order_id": order["id"],
            "service_id": item["service_id"],
            "package_id": item.get("package_id"),
            "addon_id": item.get("addon_id"),
            "price": item.get("quantity", 1),
        }).execute()

    # 5. Clear cart items
    supabase.table("cart_items").delete().eq(
        "cart_id", cart["id"]
    ).execute()

    return order


# --------------------
# Get Order by ID
# --------------------
@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: UUID):
    resp = (
        supabase
        .table("orders")
        .select("*, order_items(*)")
        .eq("id", str(order_id))
        .single()
        .execute()
    )

    if not resp.data:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return resp.data


# --------------------
# List Orders by User
# --------------------
@router.get("/", response_model=List[OrderOut])
def list_orders(user_id: UUID = Query(...)):
    resp = (
        supabase
        .table("orders")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    return resp.data or []