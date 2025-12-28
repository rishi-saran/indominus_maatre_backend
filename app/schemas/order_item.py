from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class OrderItemOut(BaseModel):
    id: UUID
    service_id: UUID
    package_id: Optional[UUID] = None
    addon_id: Optional[UUID] = None
    price: float

    class Config:
        from_attributes = True