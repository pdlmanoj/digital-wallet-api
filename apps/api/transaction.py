import random
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.security import get_current_user, get_db
from apps.models.transaction import Transaction
from apps.models.user import User
from apps.models.wallet import Wallet
from apps.schemas.transaction import DepositMoneySchema, WithdrawnMoneySchema

CALLBACK_MOCK = ["success", "failed"]

router = APIRouter(prefix="/transaction", tags=["Transaction"])


def generate_reference_id():
    return f"TRAN{datetime.now().strftime('%Y%m%d%I%M')}{uuid4().hex[:12].upper()}"  # noqa: DTZ005


def get_transaction_by_ref_id(ref_id: str, db: Session):
    transaction = db.execute(
        select(Transaction).where(Transaction.reference_id == ref_id)
    ).scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No transaction found"
        )

    return transaction


def get_user_wallet(user_id: UUID, db: Session):
    user_wallet = db.scalars(
        select(Wallet).where(Wallet.user_id == user_id)
    ).one_or_none()

    if not user_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You don't have any wallet associated with you account. Please create an wallet account before proceeding.",
        )

    elif not user_wallet.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your wallet account not activated. Please contact admin to active your account.",
        )

    return user_wallet


@router.post("/deposit")
def deposit(
    data: DepositMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
):
    ## TODO: add idempotency for duplicate transaction call 
    user_wallet: Wallet = get_user_wallet(is_user.id, db)

    if data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Deposit amount cannot be 0 or negative value",
        )

    reference_id = generate_reference_id()

    transaction = Transaction(
        wallet_id=user_wallet.id,
        type=data.type,
        amount=data.amount,
        status="pending",
        reference_id=reference_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    ##TODO: call a mock payment gateway (future enhancement)
    # for now mark as success directly or failed based on random pick
    callback = random.choice(CALLBACK_MOCK)
    if callback == "success":
        transaction.status = "success"
        user_wallet.balance += data.amount
        db.commit()
        return {"msg": f"Transaction Deposit of {data.currency} {data.amount} SUCCESS."}
    else:
        transaction.status = "failed"
        db.commit()
        return {
            "msg": f"Transaction Deposit of {data.currency} {data.amount} FAILED due to some issue. Please try again later.",
        }


@router.post("/withdraw")
def withdraw(
    data: WithdrawnMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
):
    user_wallet = get_user_wallet(is_user.id, db)

    if data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Deposit amount cannot be 0 or negative value",
        )

    if data.amount > user_wallet.balance:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Insufficent balance.",
        )

    reference_number = generate_reference_id()
    transaction = Transaction(
        wallet_id=user_wallet.id,
        type=data.type,
        amount=data.amount,
        status="pending",
        reference_id=reference_number,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # TODO: call payment gateway for withdraw money from wallet

    callback = random.choice(CALLBACK_MOCK)

    if callback == "success":
        user_wallet.balance -= data.amount
        transaction.status = "success"
        db.commit()

        return {
            "msg": f"The amount of {user_wallet.currency} {data.amount} withdrawn successfully. Available Balance {user_wallet.currency} {user_wallet.balance}"
        }

    else:
        transaction.status = "failed"
        db.commit()
        return {
            "msg": f"The amount of {user_wallet.currency} {data.amount} failed due to some issue. Please try again later."
        }


@router.post("/send-money")
def send_money(
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
): ...
