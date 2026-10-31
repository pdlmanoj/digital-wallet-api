from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, undefer_group

from apps.api.transaction import get_user_wallet
from apps.common.pagination.paginator import Paginator
from apps.common.pagination.schema import PaginatedResponseSchema
from apps.core.rate_limit import limiter
from apps.core.security import get_admin
from apps.db.session import get_db
from apps.models.user import User
from apps.models.wallet import Wallet
from apps.schemas.user import UserResponseSchema
from apps.schemas.wallet import WalletListReadSchema

router = APIRouter(prefix="/manage", tags=["Admin"])


@router.get("/users", response_model=PaginatedResponseSchema[UserResponseSchema])
@limiter.limit("20/minute")
def get_users(
    request: Request,
    _: Annotated[User, Depends(get_admin)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 5,
):
    smth = select(User).options(undefer_group("timestamps"))
    return Paginator(db, page, page_size).paginated_response(smth)


@router.get("/{id}/details", response_model=UserResponseSchema)
@limiter.limit("20/minute")
def get_user(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_admin)],
) -> UserResponseSchema:
    user = db.scalar(
        select(User).options(undefer_group("timestamps")).where(User.id == id)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_type": "user.not_found", "msg": "User not found"},
        )

    return UserResponseSchema.model_validate(user)


@router.post("/inactive-user/{id}")
@limiter.limit("20/minute")
def inactive_user(
    request: Request,
    id: UUID,
    _: Annotated[User, Depends(get_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.scalar(select(User).where(User.id == id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_type": "user.not_found", "msg": "User not found"},
        )

    if user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "user.already_inactive",
                "msg": "User already inactive",
            },
        )
    user.status = "inactive"
    db.commit()

    return {"msg": "User inactivated successfully."}


@router.post("/reactivate-user/{id}")
@limiter.limit("20/minute")
def reactivate_user(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_admin)],
):

    user = db.scalar(select(User).where(User.id == id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_type": "user.not_found", "msg": "User not found"},
        )

    if user.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "user.already_inactive",
                "msg": "User already inactive",
            },
        )
    user.status = "active"
    db.commit()

    return {"msg": "User reactivated successfully."}


@router.get("/user-wallet/{id}", response_model=WalletListReadSchema)
@limiter.limit("20/minute")
def user_wallets(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_admin)],
) -> WalletListReadSchema:
    user_wallet = get_user_wallet(id, db)
    return WalletListReadSchema.model_validate(user_wallet)


@router.post("/wallet-activate/{id}")
@limiter.limit("20/minute")
def activate(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_admin)],
) -> dict:
    user_wallet = db.scalars(select(Wallet).where(Wallet.user_id == id)).one()

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


@router.post("/wallet-deactivate/{id}")
@limiter.limit("20/minute")
def deactivate(
    request: Request,
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_admin)],
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
