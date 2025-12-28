from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.order_item import OrderItemOut


class OrderOut(BaseModel):
    id: UUID
    user_id: UUID
    provider_id: Optional[UUID]
    address_id: Optional[UUID]
    total_amount: float
    status: str
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True