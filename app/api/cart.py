from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import supabase
from app.schemas.cart import CartOut
from app.schemas.cart_item import CartItemOut

router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)

# --------------------
# Get or Create Cart
# --------------------
@router.post("/", response_model=CartOut)
def create_or_get_cart(
    user_id: UUID = Query(...),
):
    # Try to fetch existing cart
    response = (
        supabase
        .table("carts")
        .select("*")
        .eq("user_id", str(user_id))
        .single()
        .execute()
    )

    if response.data:
        return response.data

    # Create new cart if not exists
    create_resp = (
        supabase
        .table("carts")
        .insert({"user_id": str(user_id)})
        .single()
        .execute()
    )

    if create_resp.error:
        raise HTTPException(
            status_code=500,
            detail=create_resp.error.message,
        )

    return create_resp.data


# --------------------
# Get Cart with Items
# --------------------
@router.get("/", response_model=CartOut)
def get_user_cart(
    user_id: UUID = Query(...),
):
    response = (
        supabase
        .table("carts")
        .select(
            "*, cart_items(*)"
        )
        .eq("user_id", str(user_id))
        .single()
        .execute()
    )

    if response.error:
        raise HTTPException(
            status_code=404,
            detail="Cart not found",
        )

    return response.data


# --------------------
# Add Item to Cart
# --------------------
@router.post("/items", response_model=CartItemOut)
def add_item_to_cart(
    cart_id: UUID = Query(...),
    service_id: UUID = Query(...),
    package_id: UUID | None = Query(None),
    addon_id: UUID | None = Query(None),
    quantity: int = Query(1, ge=1),
):
    payload = {
        "cart_id": str(cart_id),
        "service_id": str(service_id),
        "quantity": quantity,
    }

    if package_id:
        payload["package_id"] = str(package_id)
    if addon_id:
        payload["addon_id"] = str(addon_id)

    response = (
        supabase
        .table("cart_items")
        .insert(payload)
        .single()
        .execute()
    )

    if response.error:
        raise HTTPException(
            status_code=500,
            detail=response.error.message,
        )

    return response.data


# --------------------
# Remove Item from Cart
# --------------------
@router.delete("/items/{item_id}")
def remove_item_from_cart(item_id: UUID):
    response = (
        supabase
        .table("cart_items")
        .delete()
        .eq("id", str(item_id))
        .execute()
    )

    if response.error:
        raise HTTPException(
            status_code=500,
            detail=response.error.message,
        )

    return {"status": "item removed"}