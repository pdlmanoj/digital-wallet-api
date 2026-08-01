from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from apps.core.security import create_token, get_current_user, validate_refresh_token
from apps.db.session import get_db
from apps.models.user import User
from apps.repositories.db import authenticate_user
from apps.utils.utils import record_success_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def token(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = authenticate_user(data.username, data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Sorry, your account status is {user.status}. Please contact admin to reactivate you account.",
        )
    else:
        record_success_password(user, db)

    access_token = create_token(data={"sub": str(user.id), "name": user.name})
    refresh_token = create_token(
        data={"sub": str(user.id), "name": user.name}, token_type="refresh"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me")
def get_user_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return {"msg": f"Hello, {current_user.name}"}


@router.post("/refresh")
def refresh_token(
    refresh_token: Annotated[str, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
):
    access_token = validate_refresh_token(refresh_token, db)
    return {"access_token": access_token, "token_type": "Bearer"}
