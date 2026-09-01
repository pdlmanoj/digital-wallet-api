import redis
from dotenv import load_dotenv

from apps.core.config import redis_settings

load_dotenv()

redis_cache = redis.from_url(
    redis_settings.redis_url,
    decode_responses=True,
)
