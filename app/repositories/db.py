from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import password_security
from app.models import User
from app.utils.utils import record_failed_password


def authenticate_user(email: str, password: str, db: Session):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        return False

    if not password_security.verify_password(password, user.password):
        record_failed_password(user, db)
        return False

    return user


def is_user_exist(email: str, db: Session) -> bool:
    user = db.scalar(select(User).where(User.email == email))
    return bool(user)
