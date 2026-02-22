from collections import defaultdict
from datetime import datetime, timedelta
import logging

from fastapi import HTTPException, Request
import redis
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.local_requests = defaultdict(list)
        self.cleanup_interval = timedelta(minutes=5)
        self.last_cleanup = datetime.utcnow()
        self.redis_client = None
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
        except Exception as exc:
            logger.warning("Redis rate limiting unavailable, using in-memory fallback: %s", exc)
            self.redis_client = None

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/", "/docs", "/openapi.json"}:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()

        if self.redis_client:
            self._enforce_redis_limit(client_ip, now)
        else:
            self._enforce_memory_limit(client_ip, now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        return response

    def _enforce_redis_limit(self, client_ip: str, now: datetime):
        key = f"ratelimit:{client_ip}:{now.strftime('%Y%m%d%H%M')}"
        pipe = self.redis_client.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, 120)
        count, _ = pipe.execute()
        remaining = self.requests_per_minute - int(count)
        if remaining < 0:
            raise HTTPException(status_code=429, detail="Too many requests")

    def _enforce_memory_limit(self, client_ip: str, now: datetime):
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup()

        cutoff = now - timedelta(minutes=1)
        self.local_requests[client_ip] = [ts for ts in self.local_requests[client_ip] if ts > cutoff]
        if len(self.local_requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")

        self.local_requests[client_ip].append(now)

    def _cleanup(self):
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        for ip in list(self.local_requests.keys()):
            self.local_requests[ip] = [ts for ts in self.local_requests[ip] if ts > cutoff]
            if not self.local_requests[ip]:
                del self.local_requests[ip]
        self.last_cleanup = datetime.utcnow()
