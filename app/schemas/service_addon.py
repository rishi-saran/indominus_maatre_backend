from uuid import UUID
from pydantic import BaseModel


class ServiceAddonOut(BaseModel):
    id: UUID
    service_id: UUID
    name: str
    price: float

    class Config:
        from_attributes = True