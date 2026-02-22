"""Security middleware for production-grade protection."""
import time
import hashlib
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        if settings.SECURE_HEADERS_ENABLED:
            # HSTS - Force HTTPS
            if settings.ENFORCE_HTTPS:
                response.headers["Strict-Transport-Security"] = (
                    f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains; preload"
                )
            
            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # XSS Protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer Policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Permissions Policy
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=()"
            )
            
            # Content Security Policy
            if settings.CSP_ENABLED:
                csp_directives = [
                    "default-src 'self'",
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                    "style-src 'self' 'unsafe-inline'",
                    "img-src 'self' data: https:",
                    "font-src 'self' data:",
                    "connect-src 'self' wss: ws:",
                    "frame-ancestors 'none'",
                    "base-uri 'self'",
                    "form-action 'self'"
                ]
                response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if settings.ENFORCE_HTTPS and settings.is_production:
            if request.url.scheme == "http":
                url = request.url.replace(scheme="https")
                return JSONResponse(
                    status_code=status.HTTP_301_MOVED_PERMANENTLY,
                    content={"detail": "Redirecting to HTTPS"},
                    headers={"Location": str(url)}
                )
        
        return await call_next(request)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests."""
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"}
            )
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"
            ]
            
            if not any(ct in content_type for ct in allowed_types):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "Unsupported media type"}
                )
        
        return await call_next(request)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist/blacklist middleware."""
    
    def __init__(self, app, whitelist: list = None, blacklist: list = None):
        super().__init__(app)
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        
        # Check blacklist first
        if client_ip in self.blacklist:
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Check whitelist if configured
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        return await call_next(request)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID")
        
        if not request_id:
            # Generate request ID from timestamp and client info
            timestamp = str(time.time())
            client_info = f"{request.client.host}{request.url.path}"
            request_id = hashlib.sha256(
                f"{timestamp}{client_info}".encode()
            ).hexdigest()[:16]
        
        # Store request ID in request state
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """API key authentication for IoT devices and external integrations."""
    
    EXEMPT_PATHS = ["/docs", "/redoc", "/openapi.json", "/health", "/"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)
        
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        
        if not api_key and request.url.path.startswith("/api/v1/ingest"):
            # IoT ingestion endpoints require API key
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key required"}
            )
        
        if api_key:
            # Validate API key (implement your validation logic)
            # This is a placeholder - implement actual validation
            request.state.api_key = api_key
        
        return await call_next(request)


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """Basic DDoS protection through request rate monitoring."""
    
    def __init__(self, app, max_requests_per_second: int = 100):
        super().__init__(app)
        self.max_requests_per_second = max_requests_per_second
        self.request_counts = {}
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        current_time = time.time()
        client_ip = request.client.host
        
        # Cleanup old entries every 60 seconds
        if current_time - self.last_cleanup > 60:
            self.request_counts.clear()
            self.last_cleanup = current_time
        
        # Track requests per IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Remove requests older than 1 second
        self.request_counts[client_ip] = [
            t for t in self.request_counts[client_ip]
            if current_time - t < 1.0
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.max_requests_per_second:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}: "
                f"{len(self.request_counts[client_ip])} requests/second"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"},
                headers={"Retry-After": "1"}
            )
        
        # Record this request
        self.request_counts[client_ip].append(current_time)
        
        return await call_next(request)


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Basic SQL injection detection and prevention."""
    
    SQL_PATTERNS = [
        "' OR '1'='1",
        "'; DROP TABLE",
        "' OR 1=1--",
        "UNION SELECT",
        "'; EXEC",
        "<script>",
        "javascript:",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check query parameters
        query_string = str(request.url.query).lower()
        
        for pattern in self.SQL_PATTERNS:
            if pattern.lower() in query_string:
                logger.warning(
                    f"Potential SQL injection detected from {request.client.host}: "
                    f"{pattern}"
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request"}
                )
        
        return await call_next(request)


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS security with origin validation."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        if origin and settings.is_production:
            # In production, validate origin against whitelist
            allowed_origins = settings.CORS_ORIGINS
            
            if "*" not in allowed_origins and origin not in allowed_origins:
                logger.warning(f"Blocked request from unauthorized origin: {origin}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Origin not allowed"}
                )
        
        return await call_next(request)
