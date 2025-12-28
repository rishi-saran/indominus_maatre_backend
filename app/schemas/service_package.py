from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class ServicePackageOut(BaseModel):
    id: UUID
    service_id: UUID
    name: str
    price: float
    description: Optional[str] = None

    class Config:
        from_attributes = True