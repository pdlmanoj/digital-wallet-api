from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.security import get_admin, get_current_user
from apps.db.session import get_db
from apps.models.user import User
from apps.models.wallet import Wallet
from apps.schemas.wallet import (
    CreateWalletFormSchema,
    WalletDetailReadSchema,
    WalletListReadSchema,
)

router = APIRouter(prefix="/wallet", tags=["Wallet"])


def get_user_wallet(id: UUID, db: Session):
    smth = select(Wallet).where(Wallet.user_id == id)
    query = db.scalars(smth).one_or_none()
    return query


@router.post("/create")
def create(
    wallet_form: CreateWalletFormSchema,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if wallet_form.balance <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Balance cannot be negative or 0",
        )

    query = get_user_wallet(current_user.id, db)

    if query:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="It seems you already have a wallet account with us. You can't recreate new wallet again.",
        )

    wallet = Wallet(
        user_id=current_user.id,
        currency=wallet_form.currency if wallet_form.currency else "NPR",
        balance=wallet_form.balance,
    )

    db.add(wallet)
    db.commit()

    return {
        "msg": f"Wallet created successfully with initial balance of {wallet_form.currency} {wallet_form.balance}."
    }


@router.get("/details", response_model=WalletDetailReadSchema)
def details(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    query = get_user_wallet(current_user.id, db)

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet registrated for this user.",
        )

    return query


@router.get("/{id}", response_model=WalletListReadSchema)
def user_wallets(
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    is_admin: Annotated[User, Depends(get_admin)],
):
    query = get_user_wallet(id, db)

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet registrated for this user.",
        )

    return query


@router.post("/activate/{id}")
def activate(
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    is_admin: Annotated[User, Depends(get_admin)],
):
    query = get_user_wallet(id, db)

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet registrated for this user.",
        )
    if not query.is_active:
        query.is_active = True
        db.commit()
        return {"msg": "Wallet activated successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet already activated."
        )


@router.post("/deactivate/{id}")
def deactivate(
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    is_admin: Annotated[User, Depends(get_admin)],
):
    query = get_user_wallet(id, db)

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet registrated for this user.",
        )
    if query.is_active:
        query.is_active = False
        db.commit()
        return {"msg": "Wallet deactivated successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet already deactivated.",
        )

# TODO: default wallet , multi currency wallet support

#######################################################

