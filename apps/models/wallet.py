from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.db.session import Base

if TYPE_CHECKING:
    from apps.models.user import User


class Wallet(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    currency: Mapped[str] = mapped_column(server_default="NPR")
    balance: Mapped[Decimal] = mapped_column(Numeric(precision=6, scale=2))
    is_active: Mapped[bool] = mapped_column(server_default=true())
    user: Mapped["User"] = relationship(back_populates="user_wallet")
