from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field, field_validator

from apps.core.pydantic import Schema
from apps.schemas.wallet import WalletProfileSchema


class UserCreateSchema(Schema):
    name: str
    email: EmailStr
    password: str
    phone_number: str = Field(min_length=10, max_length=10)
    gender: str
    date_of_birth: date

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v):
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.strip().lower()

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v not in ["male", "female", "other"]:
            raise ValueError("Invalid gender. Must be 'male', 'female', or 'other'.")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        if len(v) != 10:
            raise ValueError("Invalid phone number.")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        if v > datetime.now(tz=UTC).date():
            raise ValueError("Date of birth cannot be in the future.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password length must be greater than 8 characters.")

        return v

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


class UserProfileResponseSchema(Schema):
    name: str
    email: EmailStr
    phone_number: str
    gender: str
    date_of_birth: date
    status: Literal["active", "inactive"]
    is_2fa_enable: bool
    wallet: WalletProfileSchema | None = Field(validation_alias="user_wallet")


class UserResponseSchema(UserProfileResponseSchema):
    id: UUID
