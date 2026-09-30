from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from apps.core.config import redis_settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_settings.redis_url,
)


def customer_rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    exc.detail = "Too many requests. Please try again later."
    return _rate_limit_exceeded_handler(request, exc)
