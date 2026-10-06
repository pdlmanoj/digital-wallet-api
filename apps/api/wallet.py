from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.transaction import generate_reference_id
from apps.core.rate_limit import limiter
from apps.core.security import get_admin, get_current_user
from apps.db.session import get_db
from apps.models import User, Wallet
from apps.models.transaction import Transaction
from apps.schemas.wallet import (
    AvailableBalanceReadSchema,
    CreateWalletFormSchema,
    WalletListReadSchema,
)

router = APIRouter(prefix="/wallet", tags=["Wallet"])


def get_user_wallet(id: UUID, db: Session):
    user_wallet = db.scalar(select(Wallet).where(Wallet.user_id == id))

    if not user_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "wallet.not_found",
                "msg": "No wallet registrated for this user.",
            },
        )
    return user_wallet


@router.post("/create")
@limiter.limit("5/minute")
def create(
    request: Request,
    data: CreateWalletFormSchema,
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
) -> dict:

    user_wallet = db.scalar(select(Wallet).where(Wallet.user_id == is_user.id))

    if user_wallet:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_type": "wallet.already_exists",
                "msg": "It seems you already have a wallet account with us. You can't recreate new wallet again.",
            },
        )

    wallet = Wallet(
        user_id=is_user.id,
        currency=data.currency if data.currency else "NPR",
        balance=data.amount,
    )

    db.add(wallet)

    transaction = Transaction(
        wallet_id=wallet.id,
        type="deposit",
        amount=data.amount,
        reference_id=generate_reference_id(),
        status="success",
    )
    db.add(transaction)
    db.commit()

    return {
        "msg": f"Wallet successfully created with initial balance of {data.currency} {data.amount}."
    }


@router.get("/check-balance", response_model=AvailableBalanceReadSchema)
@limiter.limit("20/minute")
def check_balance(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
) -> AvailableBalanceReadSchema:
    user_wallet = get_user_wallet(is_user.id, db)

    return AvailableBalanceReadSchema.model_validate(user_wallet)


@router.get("/{id}", response_model=WalletListReadSchema)
@limiter.limit("20/minute")
def user_wallets(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    is_admin: Annotated[User, Depends(get_admin)],
) -> WalletListReadSchema:
    user_wallet = get_user_wallet(id, db)
    return WalletListReadSchema.model_validate(user_wallet)


@router.post("/activate/{id}")
@limiter.limit("3/minute")
def activate(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    is_admin: Annotated[User, Depends(get_admin)],
) -> dict:
    user_wallet = get_user_wallet(id, db)

    if not user_wallet.is_active:
        user_wallet.is_active = True
        db.commit()
        return {"msg": "User wallet activated successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "wallet.already_activated",
                "msg": "Wallet already activated.",
            },
        )


@router.post("/deactivate/{id}")
@limiter.limit("3/minute")
def deactivate(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    is_admin: Annotated[User, Depends(get_admin)],
) -> dict:
    user_wallet = get_user_wallet(id, db)

    if not user_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "wallet.not_found",
                "msg": "No wallet registrated for this user.",
            },
        )
    if user_wallet.is_active:
        user_wallet.is_active = False
        db.commit()
        return {"msg": "User wallet deactivated successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "wallet.already_deactivated",
                "msg": "Wallet already deactivated.",
            },
        )


# TODO: default wallet , multi currency wallet support

#######################################################
