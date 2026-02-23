import asyncio
from contextlib import asynccontextmanager
import json
import logging
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    admin,
    alerts,
    analytics,
    auth,
    dashboard,
    devices,
    geo,
    incidents,
    ingest,
    iot_protocols,
    maintenance,
    monitoring,
    municipalities,
    pipelines,
    preferences,
    realtime,
    reports,
    roles,
    sensors,
    settings,
    advanced_analytics,
    system_utilities,
    batch_operations,
)
from .core.config import settings as app_settings
from .core.database import Base, SessionLocal, engine
from .core.security import decode_token
from .middleware.logging import LoggingMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.security import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware,
    RequestValidationMiddleware,
    RequestIDMiddleware,
    DDoSProtectionMiddleware,
    SQLInjectionProtectionMiddleware,
)
from .models.user import User
from .mqtt.client import mqtt_client
from .websocket.manager import ws_manager
from .services.metrics_service import metrics_service
from .services.prometheus_metrics import get_metrics_endpoint
from .services.audit_service import AuditLoggingMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_tcp_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tcp_task
    logger.info("Starting %s", app_settings.APP_NAME)

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database connected and schema verified")
    except Exception as e:
        logger.error("❌ Database connection failed: %s", e)
        logger.warning("Continuing without database initialization...")

    loop = asyncio.get_event_loop()
    ws_manager.set_event_loop(loop)

    try:
        mqtt_client.connect()
        logger.info("✅ MQTT client connected")
    except Exception as e:
        logger.info("ℹ️ MQTT broker not configured (optional)")

    try:
        from .tcp.server import tcp_server

        _tcp_task = asyncio.create_task(tcp_server.start())
        logger.info("TCP server started on %s:%s", app_settings.TCP_HOST, app_settings.TCP_PORT)
    except Exception as exc:
        logger.warning("TCP server failed to start: %s", exc)

    yield

    if _tcp_task and not _tcp_task.done():
        _tcp_task.cancel()
        try:
            await _tcp_task
        except asyncio.CancelledError:
            pass

    mqtt_client.disconnect()
    logger.info("Shutdown complete")


app = FastAPI(
    title=app_settings.APP_NAME,
    version=app_settings.APP_VERSION,
    description="National Water Infrastructure Monitoring System API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware stack (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
if app_settings.is_production:
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(SQLInjectionProtectionMiddleware)
app.add_middleware(DDoSProtectionMiddleware, max_requests_per_second=100)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(RequestIDMiddleware)

# Application middleware
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=app_settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(LoggingMiddleware)


# Metrics middleware for Prometheus monitoring
@app.middleware("http")
async def add_metrics_middleware(request: Request, call_next):
    """Record HTTP metrics for Prometheus monitoring."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Record metrics only if metrics service is available
    if app_settings.PROMETHEUS_ENABLED:
        metrics_service.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )
    
    return response

app.include_router(auth.router, prefix="/api/v1")
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(pipelines.router, prefix="/api/v1")
app.include_router(municipalities.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
app.include_router(geo.router)
app.include_router(dashboard.router)
app.include_router(preferences.router)
app.include_router(iot_protocols.router)
app.include_router(maintenance.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(realtime.router, prefix="/api/v1")
app.include_router(advanced_analytics.router)
app.include_router(system_utilities.router)
app.include_router(batch_operations.router)


@app.get("/")
async def root():
    return {
        "name": app_settings.APP_NAME,
        "version": app_settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if app_settings.PROMETHEUS_ENABLED:
        return get_metrics_endpoint()
    return {"error": "Metrics disabled"}


def _authenticate_websocket(token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None

        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        finally:
            db.close()
    except Exception:
        return None


@app.websocket("/ws/{municipality_id}")
async def websocket_endpoint(websocket: WebSocket, municipality_id: str):
    token = websocket.query_params.get("token")
    user = _authenticate_websocket(token)
    if not user:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    if municipality_id == "global" and not user.is_super_admin:
        await websocket.close(code=1008, reason="Forbidden")
        return

    if municipality_id != "global" and (not user.is_super_admin) and user.municipality_id != municipality_id:
        await websocket.close(code=1008, reason="Forbidden")
        return

    target_scope = municipality_id if user.is_super_admin else user.municipality_id

    await ws_manager.connect(websocket, target_scope)

    replay_limit = min(int(websocket.query_params.get("replay_limit", "50")), 500)
    replay_events = ws_manager.get_events(target_scope, limit=replay_limit)
    await ws_manager.send_personal_message(
        {"type": "replay", "data": replay_events},
        websocket,
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws_manager.send_personal_message({"type": "pong"}, websocket)
            except Exception:
                await ws_manager.send_personal_message({"type": "error", "detail": "Invalid message format"}, websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
