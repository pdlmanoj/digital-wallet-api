from io import BytesIO
from typing import Annotated

import pyotp
import qrcode
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.rate_limit import limiter
from apps.core.redis import redis_cache
from apps.core.security import (
    create_token,
    generate_temporary_token,
    get_current_user,
    validate_refresh_token,
    validate_two_factor_token,
)
from apps.db.session import get_db
from apps.models import User
from apps.repositories.db import authenticate_user
from apps.schemas.auth import Token2FAResponseSchema, TokenResponseSchema
from apps.schemas.user import UserProfileResponseSchema
from apps.utils.utils import record_success_password

router = APIRouter(prefix="/auth", tags=["Auth"])

TOTP_KEY = "2fa-enable:{id}"
EXPIRE_IN = 300


@router.post("/login", response_model=TokenResponseSchema | Token2FAResponseSchema)
@limiter.limit("5/minute")
def token(
    request: Request,
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponseSchema | Token2FAResponseSchema:
    user: User | bool = authenticate_user(data.username, data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_type": "auth.invalid_credentials",
                "msg": "Invalid username or password",
            },
        )

    if user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_type": "auth.inactive_user",
                "msg": "Your account is inactive. Please contact admin to reactivate your account.",
            },
        )
    else:
        record_success_password(user, db)

    if user.is_2fa_enable:
        temp_token = generate_temporary_token(user.id)
        return {
            "is_2fa_enable": user.is_2fa_enable,
            "token": temp_token,
            "required_2fa_verification": True,
        }

    payload = {"sub": str(user.id), "name": user.name}
    access_token = create_token(payload)
    refresh_token = create_token(payload, token_type="refresh")

    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserProfileResponseSchema)
@limiter.limit("20/minute")
def get_user_profile(
    request: Request, user: Annotated[User, Depends(get_current_user)]
) -> UserProfileResponseSchema:
    return UserProfileResponseSchema.model_validate(user)


@router.post("/refresh")
@limiter.limit("5/minute")
def refresh_token(
    request: Request,
    refresh_token: Annotated[str, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    access_token = validate_refresh_token(refresh_token, db)
    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/enable-2fa")
@limiter.limit("5/minute")
def enable_2fa(
    request: Request, user: Annotated[User, Depends(get_current_user)]
) -> StreamingResponse:
    if user.is_2fa_enable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "2FA.already_enable",
                "msg": "You have already activated 2FA for your account.",
            },
        )

    key = pyotp.random_base32()
    totp = pyotp.TOTP(key)
    uri = totp.provisioning_uri(name=user.email, issuer_name="Digital Wallet API")

    img = qrcode.make(uri)
    buffer = BytesIO()
    img.save(buffer, format="PNG")  # type: ignore
    buffer.seek(0)

    # save secrete_key in redis for 5 minute
    redis_cache.set(name=TOTP_KEY.format(id=user.id), value=key, ex=EXPIRE_IN)

    return StreamingResponse(buffer, media_type="image/png")


@router.post("/confirm-2fa")
@limiter.limit("5/minute")
def confirm_2fa(
    request: Request,
    totp: Annotated[str, Body(embed=True)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if user.is_2fa_enable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "2FA.already_enable",
                "msg": "You have already 2FA activated for your account.",
            },
        )

    key: str | None = redis_cache.get(TOTP_KEY.format(id=user.id))

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_type": "2FA.setup_required",
                "msg": "Please start the 2FA setup process before confirming your TOTP.",
            },
        )

    obj = pyotp.TOTP(key)
    is_valid = obj.verify(totp)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "2FA:totp_invalid",
                "msg": "Invalid TOTP.",
            },
        )

    user.is_2fa_enable = True
    user.secrete_key_2fa = key
    db.commit()

    return {"msg": "Your 2FA setup completed."}


@router.post("/verify-2fa", response_model=TokenResponseSchema)
@limiter.limit("5/minute")
def verify_2fa(
    request: Request,
    token: Annotated[str, Header(..., alias="X-Auth-Token")],
    totp: Annotated[str, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponseSchema:
    user_id = validate_two_factor_token(token)
    user: User | None = db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_type": "2FA.user_not_found",
                "msg": "You don't have account with us. Please register to use our app.",
            },
        )

    if not user.is_2fa_enable:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_type": "2FA.not_enable",
                "msg": "You don't have 2FA enable for your account. Please setup 2FA if you want to use it for your account.",
            },
        )

    obj = pyotp.TOTP(user.secrete_key_2fa)
    is_valid = obj.verify(totp)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_type": "2FA.totp_invalid",
                "msg": "Invalid TOTP",
            },
        )

    payload = {"sub": str(user.id), "name": user.name}

    access_token = create_token(payload)
    refresh_token = create_token(payload, token_type="refresh")

    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/disable-2fa")
@limiter.limit("5/minute")
def disable_2fa(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if not user.is_2fa_enable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "2FA.not_enable",
                "msg": "You don't have 2FA enable for your account.",
            },
        )

    user.is_2fa_enable = False
    db.commit()

    return {"msg": "Your 2FA authentication setup disable successfully."}
