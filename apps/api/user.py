from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from apps.core.security import get_admin, get_current_user, password_security
from apps.db.session import get_db
from apps.models.user import User
from apps.schemas.user import UserCreateSchema, UserResponseSchema
from apps.utils.Email.email import email as mileroo_email
from apps.utils.utils import validate_otp

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/signup", response_model=UserResponseSchema)
def create_user(user: UserCreateSchema, db: Annotated[Session, Depends(get_db)]):

    query = db.scalar(
        select(User).filter(
            or_(User.email == user.email, User.phone_number == user.phone_number)
        )
    )

    if query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="It seem you already have an account with us. Please proceed with login.",
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
def get_users(
    is_admin: Annotated[User, Depends(get_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    return db.execute(select(User)).scalars().all()


@router.get("/user/{id}", response_model=UserResponseSchema)
def get_user(id: UUID, db: Annotated[Session, Depends(get_db)]):

    smth = select(User).filter_by(id=id)

    user = db.execute(smth).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponseSchema.model_validate(user)


@router.post("/send-otp")
def send_email(email: Annotated[EmailStr, Body(embed=True)]):

    response = mileroo_email.send_email(email=email)

    if response.json().get("success") != True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email OTP send failed, try again later",
        )

    return {"msg": "OTP send successfully"}


@router.post("/verify-otp")
def verify_otp(
    email: Annotated[EmailStr, Body(embed=True)], otp: Annotated[str, Body(embed=True)]
):
    is_valid = validate_otp(email, otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP or Expired"
        )

    return {"msg": "OTP verified successfully"}


@router.post("/resend-otp")
def resend_otp(email: Annotated[EmailStr, Body(embed=True)]):

    response = mileroo_email.send_email(email=email)

    if response.json().get("success") != True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP resend failed, try again later",
        )

    return {"msg": "Resend OTP successfully"}


@router.post("/change-password")
def change_password(
    current_password: Annotated[str, Body(embed=True)],
    new_password: Annotated[str, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
):
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be greater than 8 characters.",
        )

    is_valid = password_security.verify_password(current_password, is_user.password)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your current password doesn't match.",
        )

    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot set current password as new password",
        )

    hash_password = password_security.hash_password(new_password)

    if is_user.old_password and password_security.verify_password(
        new_password, is_user.old_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You new password cannot be same as previous password. Choose different password.",
        )

    is_user.old_password = is_user.password
    is_user.password = hash_password
    db.add(is_user)
    db.commit()

    return {"msg": "Password changed successfully"}
