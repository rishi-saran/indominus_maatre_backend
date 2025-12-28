from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class ServiceProviderOut(BaseModel):
    id: UUID
    name: str
    phone: Optional[str] = None
    verified: bool

    class Config:
        from_attributes = True