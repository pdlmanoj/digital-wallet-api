from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from apps.core.rate_limit import limiter
from apps.core.security import get_admin, get_current_user, password_security
from apps.db.session import get_db
from apps.models import User
from apps.repositories.db import is_user_exist
from apps.schemas.user import UserCreateSchema, UserResponseSchema
from apps.utils.Email.email import email as mileroo_email
from apps.utils.utils import generate_random_password, validate_otp

router = APIRouter(prefix="/user", tags=["User"])


@router.post(
    "/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def create_user(
    request: Request, user: UserCreateSchema, db: Annotated[Session, Depends(get_db)]
):

    query = db.scalar(
        select(User).filter(
            or_(User.email == user.email, User.phone_number == user.phone_number)
        )
    )

    if query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "create_user.duplicate_user",
                "msg": "It seem you already have an account with us. Please proceed with login.",
            },
        )

    hash_password = password_security.hash_password(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password,
        phone_number=user.phone_number,
        gender=user.gender,
        date_of_birth=user.date_of_birth,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponseSchema.model_validate(new_user)


@router.get("/users", response_model=list[UserResponseSchema])
@limiter.limit("20/minute")
def get_users(
    request: Request,
    is_admin: Annotated[User, Depends(get_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    return db.execute(select(User)).scalars().all()


@router.get("/{id}", response_model=UserResponseSchema)
@limiter.limit("20/minute")
def get_user(request: Request, id: UUID, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.id == id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_type": "get_user.user_not_found", "msg": "User not found"},
        )

    return UserResponseSchema.model_validate(user)


@router.post("/send-otp")
@limiter.limit("2/minute")
def send_email(
    request: Request,
    email: Annotated[EmailStr, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
):
    user_exist = is_user_exist(email, db)
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "user.already_exists",
                "msg": "It seems you already have an account with us. Please proceed with login.",
            },
        )

    response = mileroo_email.send_email(email=email)

    if response.json().get("success") != True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "send_otp.send_failed",
                "msg": "Email OTP send failed, try again later",
            },
        )

    return {"msg": "OTP send successfully"}


@router.post("/verify-otp")
@limiter.limit("3/minute")
def verify_otp(
    request: Request,
    email: Annotated[EmailStr, Body(embed=True)],
    otp: Annotated[str, Body(embed=True)],
):
    is_valid = validate_otp(email, otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "verify_otp.invalid_otp",
                "msg": "Invalid OTP or Expired",
            },
        )

    return {"msg": "OTP verified successfully"}


@router.post("/resend-otp")
@limiter.limit("2/minute")
def resend_otp(
    request: Request,
    email: Annotated[EmailStr, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
):
    user_exist = is_user_exist(email, db)
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "user.already_exists",
                "msg": "It seems you already have an account with us. Please proceed with login.",
            },
        )
    response = mileroo_email.send_email(email=email)

    if response.json().get("success") != True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "resend_otp.resend_failed",
                "msg": "OTP resend failed, try again later",
            },
        )

    return {"msg": "Resend OTP successfully"}


@router.post("/change-password")
@limiter.limit("3/minute")
def change_password(
    request: Request,
    current_password: Annotated[str, Body(embed=True)],
    new_password: Annotated[str, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
):
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "change_password.password_too_short",
                "msg": "Password must be greater than 8 characters.",
            },
        )

    is_valid = password_security.verify_password(current_password, is_user.password)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "change_password.invalid_current_password",
                "msg": "Your current password doesn't match.",
            },
        )

    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "change_password.same_as_current",
                "msg": "You cannot set current password as new password",
            },
        )

    hash_password = password_security.hash_password(new_password)

    if is_user.old_password and password_security.verify_password(
        new_password, is_user.old_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "change_password.same_as_old",
                "msg": "You new password cannot be same as previous password. Choose different password.",
            },
        )

    is_user.old_password = is_user.password
    is_user.password = hash_password
    db.add(is_user)
    db.commit()

    return {"msg": "Password changed successfully"}


@router.post("/forget-password")
@limiter.limit("3/minute")
def forget_password(
    request: Request,
    email: Annotated[EmailStr, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.scalar(select(User).where(User.email == email))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "user.not_found",
                "msg": "User with this email not found.",
            },
        )

    # send random password to user email and update the password in db
    password = generate_random_password(length=12)

    response = mileroo_email.send_email(
        email, password=password, type="forgot_password"
    )

    if response.json().get("success") != True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email send failed, try again later",
        )

    hash_password = password_security.hash_password(password)
    db.add(user)
    user.old_password = user.password
    user.password = hash_password
    db.commit()

    return {"msg": "New password send to your email successfully."}
