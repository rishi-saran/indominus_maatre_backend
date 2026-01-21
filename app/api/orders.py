from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user
from app.schemas.order import OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])


# --------------------
# Create Order from Cart
# --------------------
@router.post("/", response_model=OrderOut)
def create_order(
    provider_id: UUID = Query(...),
    address_id: UUID = Query(...),
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    # 1. Fetch user's cart with items
    cart_resp = (
        supabase
        .table("carts")
        .select("id, cart_items(*)")
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if not cart_resp.data or not cart_resp.data[0]["cart_items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    cart = cart_resp.data[0]
    cart_items = cart["cart_items"]

    # 2. Calculate total amount
    total_amount = 0.0
    for item in cart_items:
        qty = int(item.get("quantity", 1))
        price = float(item.get("price", 0) or 0)
        total_amount += price * qty

    # 3. Create order
    order_payload = {
        "user_id": str(user_id),
        "provider_id": str(provider_id),
        "address_id": str(address_id),
        "total_amount": total_amount,
        "status": "CREATED",
    }

    order_resp = (
        supabase
        .table("orders")
        .insert(order_payload)
        .execute()
    )

    if not order_resp.data or len(order_resp.data) == 0:
        raise HTTPException(status_code=500, detail="Failed to create order")

    order = order_resp.data[0]

    # 4. Insert order items
    for item in cart_items:
        order_item_payload = {
            "order_id": order["id"],
            "service_id": item["service_id"],
            "package_id": item.get("package_id"),
            "addon_id": item.get("addon_id"),
            "price": float(item.get("price", 0) or 0),
        }

        supabase.table("order_items").insert(order_item_payload).execute()

    # 5. Clear cart items
    supabase.table("cart_items").delete().eq(
        "cart_id", cart["id"]
    ).execute()

    return order


# --------------------
# Get Order by ID (Owner only)
# --------------------
@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    resp = (
        supabase
        .table("orders")
        .select("*, order_items(*)")
        .eq("id", str(order_id))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="Order not found")

    return resp.data[0]


# --------------------
# List Orders by Current User
# --------------------
@router.get("/", response_model=List[OrderOut])
def list_orders(
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    resp = (
        supabase
        .table("orders")
        .select("*")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute()
    )

    return resp.data or []