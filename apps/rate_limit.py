## rate limit for learning
# fixed window

from time import time

from fastapi import HTTPException, status

from apps.core.redis import redis_cache

RATE_LIMIT_KEY = "retry-limit:{client_ip}"

# for one atomic operation
lua_script = """
local count = redis.call('INCR', KEYS[1])

if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])

end

local retry_after = redis.call('TTL', KEYS[1])

return {count, retry_after}
"""

lua_rate_limit = redis_cache.register_script(lua_script)


class Ratelimit:
    def __init__(self, ip_address: str) -> None:
        self.ip_address = ip_address
        self.window_size = 10
        self.rate_limt = 3
        self.request_origin = {}

    def check_limit_normal(self):
        now = time()

        if self.ip_address not in self.request_origin:
            self.request_origin[self.ip_address] = {
                "count": 1,
                "last_request_time": now,
            }
            return

        request_count = now - self.request_origin[self.ip_address]["last_request_time"]

        if request_count >= self.window_size:
            self.request_origin[self.ip_address] = {
                "count": 1,
                "last_request_time": now,
            }
            return

        if self.request_origin[self.ip_address]["count"] >= self.rate_limt:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        self.request_origin[self.ip_address]["count"] += 1

    def check_limit_redis(self):
        key = RATE_LIMIT_KEY.format(client_ip=self.ip_address)
        # total_hit = redis_cache.incr(key)

        # if total_hit == 1:
        #     redis_cache.expire(key, self.window_size)

        total_hit, retry_after = lua_rate_limit(keys=[key], args=[self.window_size])

        if total_hit > self.rate_limt:
            # retry_after = str(redis_cache.ttl(key))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )
