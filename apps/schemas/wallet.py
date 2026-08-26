from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict, field_validator

from apps.core.pydantic import Schema


class CreateWalletFormSchema(Schema):
    currency: str | None
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < Decimal(1):
            raise ValueError("Invalid amount.")

        return v

    model_config = ConfigDict(
        json_schema_extra={"example": {"amount": "100.00", "currency": "NPR"}}
    )


class AvailableBalanceReadSchema(CreateWalletFormSchema):
    hold_amount: Decimal = Decimal(0)
    is_active: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "balance": "100.00",
                "currency": "NPR",
                "hold_amount": 0,
                "is_active": True,
            }
        }
    )


class WalletListReadSchema(CreateWalletFormSchema):
    user_id: UUID
    is_active: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "balance": "100.00",
                "currency": "NPR",
                "user_id": "069730e8-c7d1-73b7-8000-36a999eee3b0",
                "is_active": True,
            }
        }
    )
