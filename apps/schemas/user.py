from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, EmailStr

from apps.core.pydantic import Schema


class UserCreateSchema(Schema):
    name: str
    email: EmailStr
    password: str
    phone_number: str
    gender: str
    date_of_birth: date

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Ram Sharma",
                "email": "test@gmail.com",
                "password": "myp@ss45WoRD@!",
                "phone_number": "9847284181",
                "gender": "male",
                "date_of_birth": "1999-01-01",
            }
        }
    )


class UserResponseSchema(Schema):
    id: UUID
    name: str
    email: EmailStr
    phone_number: str
    gender: str
    date_of_birth: date
    status: Literal["active", "inactive"]
