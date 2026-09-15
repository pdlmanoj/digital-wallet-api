import random
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.rate_limit import limiter
from apps.core.security import get_current_user, get_db
from apps.models import User, Wallet
from apps.models.transaction import Transaction
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
    transaction = db.scalar(
        select(Transaction).where(Transaction.reference_id == ref_id)
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "transaction.not_found",
                "msg": "No transaction found",
            },
        )

    return transaction


def get_user_wallet(user_id: UUID, db: Session):
    user_wallet = db.scalar(select(Wallet).where(Wallet.user_id == user_id))

    if not user_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "transaction.wallet_not_found",
                "msg": "You don't have any wallet associated with your account. Please create an wallet account before proceeding.",
            },
        )

    elif not user_wallet.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "transaction.wallet_not_active",
                "msg": "Your wallet account not activated. Can't proceed further.",
            },
        )

    return user_wallet


def check_receiver_user_exist(receiver: str, db: Session):
    user: User | None = db.scalar(select(User).filter(User.phone_number == receiver))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error_type": "transaction.receiver_not_found",
                "msg": "Receiver don't have associate account with us. Can't send money.",
            },
        )


def check_sufficent_balance(amount: Decimal, user_balance: Decimal):
    if amount > user_balance:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error_type": "transaction.insufficient_balance",
                "msg": "Insufficient balance.",
            },
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
            detail={
                "error_type": "transaction.receiver_wallet_not_found",
                "msg": "Receiver don't have any wallet associated with his account. Can't send money to user with no wallet.",
            },
        )

    if not receiver_wallet.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "transaction.receiver_wallet_not_active",
                "msg": "Receiver wallet account not active can't receive amount.",
            },
        )

    return receiver_wallet


@router.post("/deposit")
@limiter.limit("5/minute")
def deposit(
    request: Request,
    data: DepositMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    ## TODO: add idempotency for duplicate transaction call
    wallet: Wallet = get_user_wallet(user.id, db)

    reference_id = generate_reference_id()

    transaction = Transaction(
        wallet_id=wallet.id,
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
        wallet.balance += data.amount
        db.commit()
        return {"msg": f"Transaction Deposit of {data.currency} {data.amount} SUCCESS."}
    else:
        transaction.status = "failed"
        db.commit()
        return {
            "msg": f"Transaction Deposit of {data.currency} {data.amount} FAILED due to some issue. Please try again later.",
        }


@router.post("/withdraw")
@limiter.limit("5/minute")
def withdraw(
    request: Request,
    data: WithdrawnMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    wallet = get_user_wallet(user.id, db)
    check_sufficent_balance(data.amount, wallet.balance)

    reference_number = generate_reference_id()
    transaction = Transaction(
        wallet_id=wallet.id,
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
        wallet.balance -= data.amount
        transaction.status = "success"
        db.commit()

        return {
            "msg": f"The amount of {wallet.currency} {data.amount} withdrawn successfully."
        }

    else:
        transaction.status = "failed"
        db.commit()
        return {
            "msg": f"The amount of {wallet.currency} {data.amount} failed due to some issue. Please try again later."
        }


@router.post("/send-money")
@limiter.limit("5/minute")
def send_money(
    request: Request,
    data: SendMoneySchema,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    sender_wallet = get_user_wallet(user.id, db)
    check_receiver_user_exist(data.receiver_phone_number, db)
    receiver_wallet = get_receiver_wallet(data.receiver_phone_number, db)
    check_sufficent_balance(data.amount, sender_wallet.balance)

    sender_wallet.balance -= data.amount
    receiver_wallet.balance += data.amount
    db.commit()

    return {
        "msg": f"Amount of {sender_wallet.currency} {data.amount} send successfully to {receiver_wallet.user.name}."
    }
