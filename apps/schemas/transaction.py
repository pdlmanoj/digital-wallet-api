from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict

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
    sender_phone_number: str
    receiver_phone_number: str
    amount: Decimal

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sender_phone_number": "98576234569",
                "receiver_phone_number": "9857698786",
                "amount": "100.00",
            }
        }
    )
