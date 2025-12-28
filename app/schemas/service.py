from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class ServiceBase(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    base_price: Optional[float] = None
    is_virtual: bool
    category_id: Optional[UUID]
    provider_id: Optional[UUID]

    class Config:
        from_attributes = True