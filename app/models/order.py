import uuid
from sqlalchemy import Numeric, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base
from datetime import datetime

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id")
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("service_providers.id")
    )
    address_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("addresses.id")
    )

    total_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
    TIMESTAMP,
    server_default=func.now()
)

    items = relationship("OrderItem", cascade="all, delete")