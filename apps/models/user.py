from datetime import date
from typing import Literal
from uuid import UUID

from sqlalchemy import String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from apps.db.session import Base
from apps.models.wallet import Wallet


class User(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7, index=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    old_password: Mapped[str | None]
    phone_number: Mapped[str] = mapped_column(String(10), unique=True)
    gender: Mapped[Literal["male", "female", "other"]]
    date_of_birth: Mapped[date]
    status: Mapped[Literal["active", "inactive", "password_lock"]] = mapped_column(
        server_default="active"
    )
    is_admin: Mapped[bool] = mapped_column(server_default=false())
    login_attempt: Mapped[int] = mapped_column(server_default="0")
    user_wallet: Mapped[Wallet] = relationship(back_populates="user")
