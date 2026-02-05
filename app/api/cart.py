from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user
from app.schemas.cart import CartOut
from app.schemas.cart_item import CartItemOut

router = APIRouter(prefix="/cart", tags=["Cart"])


# --------------------
# Get or Create Cart
# --------------------
@router.post("/", response_model=CartOut)
def get_or_create_cart(
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    resp = (
        supabase
        .table("carts")
        .select("*")
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if resp.data:
        return resp.data[0]

    create_resp = (
        supabase
        .table("carts")
        .insert({"user_id": str(user_id)})
        .execute()
    )

    if not create_resp.data or len(create_resp.data) == 0:
        raise HTTPException(status_code=500, detail="Failed to create cart")

    return create_resp.data[0]


# --------------------
# Get Cart with Items
# --------------------
@router.get("/", response_model=CartOut)
def get_cart(
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    resp = (
        supabase
        .table("carts")
        .select("*")
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if not resp.data:
        # Auto-create empty cart if not found
        create_resp = (
            supabase
            .table("carts")
            .insert({"user_id": str(user_id)})
            .execute()
        )

        if not create_resp.data or len(create_resp.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create cart")

        cart = create_resp.data[0]
    else:
        cart = resp.data[0]

    items_resp = (
        supabase
        .table("cart_items")
        .select("*")
        .eq("cart_id", cart["id"])
        .execute()
    )

    cart["cart_items"] = items_resp.data or []
    return cart


# --------------------
# Add Item to Cart
# --------------------
@router.post("/items", response_model=CartItemOut)
def add_item_to_cart(
    service_id: UUID = Query(...),
    package_id: Optional[UUID] = Query(None),
    addon_id: Optional[UUID] = Query(None),
    quantity: int = Query(1, ge=1),
    price: float = Query(...),
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    cart_resp = (
        supabase
        .table("carts")
        .select("*")
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if not cart_resp.data:
        # Auto-create cart if missing to simplify client flow
        create_resp = (
            supabase
            .table("carts")
            .insert({"user_id": str(user_id)})
            .execute()
        )

        if not create_resp.data or len(create_resp.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create cart")

        cart_id = create_resp.data[0]["id"]
    else:
        cart_id = cart_resp.data[0]["id"]

    # Check if item already exists
    query = (
        supabase
        .table("cart_items")
        .select("*")
        .eq("cart_id", cart_id)
        .eq("service_id", str(service_id))
    )

    if package_id:
        query = query.eq("package_id", str(package_id))
    else:
        query = query.is_("package_id", None)

    if addon_id:
        query = query.eq("addon_id", str(addon_id))
    else:
        query = query.is_("addon_id", None)

    existing = query.limit(1).execute()

    if existing.data:
        item = existing.data[0]
        update_resp = (
            supabase
            .table("cart_items")
            .update({"quantity": item["quantity"] + quantity, "price": price})
            .eq("id", item["id"])
            .execute()
        )

        if not update_resp.data or len(update_resp.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to update cart item")

        return update_resp.data[0]

    payload = {
        "cart_id": cart_id,
        "service_id": str(service_id),
        "quantity": quantity,
        "price": price,
    }

    if package_id:
        payload["package_id"] = str(package_id)
    if addon_id:
        payload["addon_id"] = str(addon_id)

    insert_resp = (
        supabase
        .table("cart_items")
        .insert(payload)
        .execute()
    )

    if not insert_resp.data or len(insert_resp.data) == 0:
        raise HTTPException(status_code=500, detail="Failed to add item to cart")

    return insert_resp.data[0]


# --------------------
# Remove Item from Cart
# --------------------
@router.delete("/items/{item_id}")
def remove_item_from_cart(
    item_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    user_id: UUID = current_user["id"]

    check = (
        supabase
        .table("cart_items")
        .select("id, carts!inner(user_id)")
        .eq("id", str(item_id))
        .eq("carts.user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if not check.data:
        raise HTTPException(status_code=404, detail="Item not found")

    delete_resp = (
        supabase
        .table("cart_items")
        .delete()
        .eq("id", str(item_id))
        .execute()
    )

    return {"status": "item removed"}