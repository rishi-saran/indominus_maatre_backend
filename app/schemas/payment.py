from uuid import UUID
from pydantic import BaseModel


class PaymentOut(BaseModel):
    id: UUID
    order_id: UUID
    method: str
    status: str
    amount: float

    class Config:
        from_attributes = True