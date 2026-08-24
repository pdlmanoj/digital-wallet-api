from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.security import get_current_user, get_db
from apps.models import *
from apps.schemas.transaction import DepositMoneySchema

router = APIRouter(prefix="/transaction", tags=["Transaction"])


def generate_reference_id():
    return f"TRAN{datetime.now().strftime('%Y%m%d%I%M')}{uuid4().hex[:12].upper()}"  # noqa: DTZ005


def get_user_wallet(user_id: UUID, db: Session):
    wallet = db.scalars(select(Wallet).where(Wallet.user_id == user_id)).one_or_none()

    return wallet


@router.post("/deposit")
def deposit(
    data: DepositMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
):
    user_wallet = get_user_wallet(is_user.id, db)

    if not user_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You don't have any wallet associated with you account. Please create an wallet account before proceeding.",
        )

    if user_wallet and not user_wallet.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your wallet account not activated. Please contact admin for more information.",
        )

    if data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Deposit amount cannot be 0 or negative value (-)",
        )

    reference_id = generate_reference_id()

    transaction = Transaction(
        wallet_id=user_wallet.id,
        type=data.type,
        amount=data.amount,
        reference_id=reference_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    ## call a mock payment gateway


@router.post("/withdraw")
def withdraw(
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
): ...


@router.post("/send-money")
def send_money(
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
): ...
