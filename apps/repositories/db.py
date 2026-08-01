from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.core.security import password_security
from apps.models.user import User
from apps.utils.utils import record_failed_password


def authenticate_user(email: str, password: str, db: Session):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        return False

    if not password_security.verify_password(password, user.password):
        record_failed_password(user, db)
        return False

    return user
