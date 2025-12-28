from uuid import UUID
from pydantic import BaseModel

class ServiceCategoryOut(BaseModel):
    id: UUID
    name: str
    description: str | None

    class Config:
        from_attributes = True