import random
import string

from apps.core.redis import redis_cache

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
