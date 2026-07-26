from datetime import date
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from apps.db.session import Base


class User(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7, index=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    phone_number: Mapped[str]
    gender: Mapped[Literal["male", "female", "other"]]
    date_of_birth: Mapped[date]
    status: Mapped[Literal["active", "inactive"]] = mapped_column(
        server_default="active"
    )
