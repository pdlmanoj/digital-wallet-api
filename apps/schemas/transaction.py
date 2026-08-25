from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, field_validator

from apps.core.pydantic import Schema


class InitiateTransactionSchema(Schema):
    type: Literal["deposit", "withdraw"]
    amount: Decimal


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
    receiver_phone_number: str
    amount: Decimal

    @field_validator("receiver_phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if len(v) != 10:
            raise ValueError("Invalid phone number")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receiver_phone_number": "9857698786",
                "amount": "100.00",
            }
        }
    )
