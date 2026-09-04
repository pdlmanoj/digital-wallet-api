from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from apps.core.pydantic import Schema


class InitiateTransactionSchema(Schema):
    type: Literal["deposit", "withdraw"]
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < Decimal(1):
            raise ValueError("Invalid amount.")

        return v


class DepositMoneySchema(InitiateTransactionSchema):
    currency: str = "NPR"
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "deposit",
                "amount": "100.00",
                "currency": "NPR",
            }
        }
    )


class WithdrawnMoneySchema(InitiateTransactionSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": "100.00",
                "type": "withdraw",
            }
        }
    )


class SendMoneySchema(Schema):
    receiver_phone_number: str = Field(min_length=10, max_length=10)
    amount: Decimal

    @field_validator("receiver_phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if len(v) != 10:
            raise ValueError("Invalid phone number")

        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < Decimal(1):
            raise ValueError("Invalid amount.")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receiver_phone_number": "9857698786",
                "amount": "100.00",
            }
        }
    )
