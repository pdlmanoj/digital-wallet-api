from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict

from apps.core.pydantic import Schema


class CreateWalletFormSchema(Schema):
    currency: str | None
    balance: Decimal

    model_config = ConfigDict(
        json_schema_extra={"example": {"currency": "NPR", "balance": 100}}
    )


class WalletDetailReadSchema(CreateWalletFormSchema):
    hold_amount: Decimal | None = None
    is_active: bool


class WalletListReadSchema(CreateWalletFormSchema):
    user_id: UUID
    is_active: bool
