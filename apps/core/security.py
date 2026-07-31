from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
)
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.config import settings
from apps.db.session import get_db
from apps.models.user import User

ACCESS_TOKEN_SECRET_KEY = settings.access_token_secret_key
ACCESS_TOKEN_EXPIRE_IN = settings.access_token_expire_time
REFRESH_TOKEN_SECRET_KEY = settings.refresh_token_secret_key
REFRESH_TOKEN_EXPIRE_IN = settings.refresh_token_expire_time
ALGORITHM = settings.algorithm

authentication_error_message = "You must be authenticated to perform this action."
authorization_error_message = "You are not permitted to perfom this action."
oauth_schema = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class Password:
    def hash_password(self, plain_text: str) -> str:
        plain_text_byte = plain_text.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password=plain_text_byte, salt=salt).decode("utf-8")

    def verify_password(self, plain_text: str, hash_password: str) -> bool:
        plain_text_byte = plain_text.encode("utf-8")
        hash_password_byte = hash_password.encode("utf-8")

        return bcrypt.checkpw(
            password=plain_text_byte, hashed_password=hash_password_byte
        )


password_security = Password()


def create_token(
    data: dict, token_type: Literal["access", "refresh"] = "access"
) -> str:
    payload = data.copy()

    if token_type == "access":
        expire_in = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_IN)

        payload.update({"exp": expire_in, "type": token_type})

        encode_token = jwt.encode(
            payload=payload, key=ACCESS_TOKEN_SECRET_KEY, algorithm=ALGORITHM
        )
    else:  # refresh token
        expire_in = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_IN)
        payload.update({"exp": expire_in, "type": token_type})
        encode_token = jwt.encode(
            payload=payload, key=REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM
        )

    return encode_token


def decode_token(token: str, token_type: Literal["access", "refresh"] = "access"):
    secret_key = (
        REFRESH_TOKEN_SECRET_KEY if token_type == "refresh" else ACCESS_TOKEN_SECRET_KEY
    )
    try:
        payload = jwt.decode(token, key=secret_key, algorithms=[ALGORITHM])

    except ExpiredSignatureError:
        if token_type == "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

    except (InvalidTokenError, TypeError, DecodeError):
        if token_type == "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate refresh token",
            )

    return payload


def validate_refresh_token(token: str, db: Session):
    payload = decode_token(token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        )

    user_id = payload.get("sub", None)
    user = db.scalar(select(User).where(User.id == user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not active"
        )

    return create_token(data={"sub": str(user.id), "name": user.name})


def get_current_user(
    token: Annotated[str, Depends(oauth_schema)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=authentication_error_message,
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: UUID | None = payload.get("sub", None)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalars(select(User).where(User.id == user_id)).one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not active"
        )

    return user


def get_admin(
    token: Annotated[str, Depends(oauth_schema)],
    db: Annotated[Session, Depends(get_db)],
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=authentication_error_message,
        )

    payload = decode_token(token)
    user_id: User | None = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

    is_admin = db.scalar(
        select(User).where(
            User.id == user_id, User.status == "active", User.is_admin.is_(True)
        )
    )

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=authorization_error_message
        )

    return is_admin
