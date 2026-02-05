from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class OrderItemOut(BaseModel):
    id: UUID
    service_id: UUID
    package_id: Optional[UUID] = None
    addon_id: Optional[UUID] = None
    quantity: int = 1
    price: float

    class Config:
        from_attributes = True