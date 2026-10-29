import random
import string

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Query, Session

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
            detail={
                "error_type": "auth.password_lock",
                "msg": "Your account has been locked due to multiple failed login attempts. Please contact admin to unlock your account.",
            },
        )
    db.commit()


def record_success_password(user: User, db: Session):
    if user.login_attempt != 0:
        user.login_attempt = 0
        user.status = "active"
        db.commit()


def generate_random_password(length: int = 12) -> str:
    letters = string.ascii_letters
    digits = string.digits
    special_chars = "!#$%&&^()"

    combined = letters + digits + special_chars

    password = "".join(random.choices(combined, k=length))

    return password


class Paginator:
    def __init__(self, db: Session, page: int, page_size: int):
        self.db = db
        self.page = page
        self.page_size = page_size

    def _get_results(self, query: Query):
        return query.all()

    def _get_pagination_query(self, query: Query):
        offset = (self.page - 1) * self.page_size
        self.count = self.db.scalar(select(func.count()).select_from(query.subquery()))
        self.total_pages = (int(self.count) + self.page_size - 1) // self.page_size
        return self.db.scalars(query.offset(offset).limit(self.page_size))

    def paginated_response(self, query: Query):
        paginated_query = self._get_pagination_query(query)
        response = {
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.count,
                "total_pages": self.total_pages,
            },
            "results": self._get_results(paginated_query),
        }

        return response
