from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.security import password_security
from apps.models.user import User


def authenticate_user(email: str, password: str, db: Session):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        return False

    if not password_security.verify_password(password, user.password):
        return False

    return user
