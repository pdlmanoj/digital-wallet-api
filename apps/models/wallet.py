from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, true
from sqlalchemy.orm import Mapped, mapped_column

from apps.db.session import Base

from .user import User


class Wallet(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey(User.id))
    currency: Mapped[str] = mapped_column(server_default="NPR")
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=6, scale=2))
    is_active: Mapped[bool] = mapped_column(server_default=true())
