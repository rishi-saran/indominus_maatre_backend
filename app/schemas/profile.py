from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


# ---- Base ----
class ProfileBase(BaseModel):
    role: Optional[str] = None


# ---- Read (what you send to frontend) ----
class ProfileResponse(ProfileBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Update (what user can change) ----
class ProfileUpdate(ProfileBase):
    pass
