from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from apps.core.security import password_security
from apps.db.session import get_db
from apps.models.user import User
from apps.schemas.user import UserCreateSchema, UserResponseSchema
from apps.utils.Email.email import email as mileroo_email
from apps.utils.utils import validate_otp

router = APIRouter(prefix="/users", tags=["User"])


@router.post("/signup", response_model=UserResponseSchema)
def create_user(user: UserCreateSchema, db: Annotated[Session, Depends(get_db)]):

    # create user
    smth = select(User).filter(
        or_(User.email == user.email, User.phone_number == user.phone_number)
    )

    query = db.execute(smth).scalars().one_or_none()  # type: ignore

    if query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
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
def get_users(db: Annotated[Session, Depends(get_db)]):

    return db.execute(select(User)).scalars().all()


@router.get("/user/{id}", response_model=UserResponseSchema)
def get_user(id: UUID, db: Annotated[Session, Depends(get_db)]):

    smth = select(User).filter_by(id=id)

    user = db.execute(smth).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP"
        )

    return {"msg": "OTP verified successfully"}
