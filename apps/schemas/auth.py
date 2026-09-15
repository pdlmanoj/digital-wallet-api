from pydantic import ConfigDict

from apps.core.pydantic import Schema


class TokenResponseSchema(Schema):
    access_token: str
    refresh_token: str
    type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbG.eyJzdLCJ0eXAi.eyJfh12XX",
                "refresh_token": "eyJhbG.eyJzdWIiOi.eyJfh12XX",
                "type": "bearer",
            }
        }
    )


class Token2FAResponseSchema(Schema):
    is_2fa_enable: bool
    token: str
    required_2fa_verification: bool = True
