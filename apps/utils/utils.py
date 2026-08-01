import random
import string

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.core.redis import redis_cache
from apps.models.user import User

EMAIL_VERIFICATION_OTP_EXPIRED_IN = 300
EMAIL_VERIFICATION_KEY = "signup-email:{email}"


def generate_otp_and_save(email: str, length: int = 6) -> str:
    otp = "".join(random.choices(string.digits, k=length))
    key = EMAIL_VERIFICATION_KEY.format(email=email)
    redis_cache.set(key, otp, ex=EMAIL_VERIFICATION_OTP_EXPIRED_IN)
    return otp


def validate_otp(email: str, otp: str) -> bool:
    key = EMAIL_VERIFICATION_KEY.format(email=email)
    cached_opt = redis_cache.get(key)
    if cached_opt and cached_opt == otp:
        # delete otp cache
        redis_cache.delete(key)
        return True

    return False


def record_failed_password(user: User, db: Session):
    user.login_attempt += 1
    if user.login_attempt >= 3:
        user.status = "password_lock"
        db.commit()
        db.refresh(user)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Sorry, your account status is {user.status}. Please contact admin to reactivate you account.",
        )
    db.commit()


def record_success_password(user: User, db: Session):
    user.login_attempt = 0
    user.status = "active"
    db.commit()
