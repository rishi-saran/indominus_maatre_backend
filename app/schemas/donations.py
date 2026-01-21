from pydantic import BaseModel
from uuid import UUID
from typing import Optional


# ---- Base ----
class DonationBase(BaseModel):
    priest_id: str
    customer_id: str
    call_id: Optional[str] = None


# ---- Create (insert) ----
class DonationCreate(DonationBase):
    pass


# ---- Read (response) ----
class DonationResponse(DonationBase):
    id: UUID

    class Config:
        from_attributes = True
