from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class AddressCreate(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str  # Frontend sends postal_code, we'll map to pincode
    country: Optional[str] = None  # Accept but don't store
    landmark: Optional[str] = None  # Accept but don't store


class AddressOut(BaseModel):
    id: UUID
    user_id: UUID
    address: str  # Database column name
    city: str
    state: str
    pincode: str  # Database column name

    class Config:
        from_attributes = True
