from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict

from apps.core.pydantic import Schema


class InitiateTransactionSchema(Schema):
    type: Literal["deposit", "withdraw"]
    amount: Decimal
    currency: str = "NPR"


class DepositMoneySchema(InitiateTransactionSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "deposit",
                "amount": "100.00",
                "currency": "NPR",
            }
        }
    )
