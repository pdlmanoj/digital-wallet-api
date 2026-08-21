from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from apps.db.session import Base
from apps.models.wallet import Wallet


class Transaction(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    wallet_id: Mapped[int] = mapped_column(ForeignKey(Wallet.id))
    type: Mapped[Literal["deposit", "withdrawn"]]
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=6, scale=2))
    status: Mapped[Literal["pending", "failed", "success"]] = mapped_column(
        server_default="pending"
    )
    reference_id: Mapped[str]
