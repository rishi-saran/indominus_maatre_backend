from uuid import UUID
from typing import List
from pydantic import BaseModel

from app.schemas.cart_item import CartItemOut


class CartOut(BaseModel):
    id: UUID
    user_id: UUID
    cart_items: List[CartItemOut] = []

    class Config:
        from_attributes = True