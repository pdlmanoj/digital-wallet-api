import random
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.security import get_current_user, get_db
from apps.models.transaction import Transaction
from apps.models.user import User
from apps.models.wallet import Wallet
from apps.schemas.transaction import (
    DepositMoneySchema,
    SendMoneySchema,
    WithdrawnMoneySchema,
)

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
            detail="You don't have any wallet associated with your account. Please create an wallet account before proceeding.",
        )

    elif not user_wallet.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your wallet account not activated. Can't proceed further.",
        )

    return user_wallet


def check_receiver_user_exist(receiver: str, db: Session):
    user: User | None = db.scalars(
        select(User).filter(User.phone_number == receiver)
    ).one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Receiver don't have associate account with us. Can't send money.",
        )


def check_sufficent_balance(amount: Decimal, user_balance: Decimal):
    if amount > user_balance:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Insufficent balance.",
        )


def get_receiver_wallet(receiver: str, db: Session):

    receiver_wallet: Wallet | None = db.scalar(
        select(Wallet)
        .join(User, Wallet.user_id == User.id)
        .where(User.phone_number == receiver)
    )
    if not receiver_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receiver don't have any wallet associated with his account. Can't send money to user with no wallet.",
        )

    if not receiver_wallet.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receiver wallet account not active can't receive amount.",
        )

    return receiver_wallet


@router.post("/deposit")
def deposit(
    data: DepositMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
):
    ## TODO: add idempotency for duplicate transaction call
    user_wallet: Wallet = get_user_wallet(is_user.id, db)

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
    check_sufficent_balance(data.amount, user_wallet.balance)

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
            "msg": f"The amount of {user_wallet.currency} {data.amount} withdrawn successfully."
        }

    else:
        transaction.status = "failed"
        db.commit()
        return {
            "msg": f"The amount of {user_wallet.currency} {data.amount} failed due to some issue. Please try again later."
        }


@router.post("/send-money")
def send_money(
    data: SendMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    is_user: Annotated[User, Depends(get_current_user)],
):
    check_receiver_user_exist(data.receiver_phone_number, db)
    receiver_wallet = get_receiver_wallet(data.receiver_phone_number, db)
    sender_wallet = get_user_wallet(is_user.id, db)
    check_sufficent_balance(data.amount, sender_wallet.balance)

    sender_wallet.balance -= data.amount
    receiver_wallet.balance += data.amount
    db.commit()

    return {
        "msg": f"Amount of {sender_wallet.currency} {data.amount} send successfully to {receiver_wallet.user.name}."
    }
