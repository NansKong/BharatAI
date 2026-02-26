"""
BharatAI FastAPI Application – Main Entrypoint
"""
import time
from contextlib import asynccontextmanager

import structlog
from app.core.config import settings
from app.core.database import close_database, engine, init_database
from app.core.logging import configure_logging
from app.core.redis import close_redis, init_redis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

configure_logging("DEBUG" if settings.DEBUG else "INFO")
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ──────────────────────────────────────────────
    logger.info(
        "Starting BharatAI backend", version=settings.APP_VERSION, env=settings.APP_ENV
    )

    await init_database()
    logger.info("Database engine initialized for app lifespan loop")

    # Initialize Redis
    await init_redis()
    logger.info("Redis connection established")

    logger.info("BharatAI backend started successfully")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    await close_redis()
    await close_database()
    logger.info("BharatAI backend shut down cleanly")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="BharatAI API",
        description="India's AI-powered academic opportunity intelligence platform",
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Prometheus middleware must be attached before app startup.
    if settings.PROMETHEUS_ENABLED:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # ── Middleware ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Rate limiting (Redis sliding window)
    from app.core.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

    # HSTS in production
    if settings.is_production:

        @app.middleware("http")
        async def hsts_middleware(request: Request, call_next):
            response = await call_next(request)
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"
            return response

    # ── Request ID + Timing middleware ────────────────────────
    @app.middleware("http")
    async def request_middleware(request: Request, call_next) -> Response:
        import uuid

        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        with structlog.contextvars.bound_contextvars(request_id=request_id):
            response = await call_next(request)

        process_time = time.monotonic() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"

        logger.info(
            "HTTP request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(process_time * 1000, 2),
        )
        return response

    # ── Routers ───────────────────────────────────────────────
    from app.api.v1 import (admin, applications, auth, community,
                            feature_flags, feed, incoscore, notifications,
                            opportunities, profile, users)

    api_prefix = "/api/v1"
    app.include_router(
        auth.router, prefix=f"{api_prefix}/auth", tags=["Authentication"]
    )
    app.include_router(users.router, prefix=f"{api_prefix}/users", tags=["Users"])
    app.include_router(profile.router, prefix=f"{api_prefix}/profile", tags=["Profile"])
    app.include_router(
        opportunities.router,
        prefix=f"{api_prefix}/opportunities",
        tags=["Opportunities"],
    )
    app.include_router(feed.router, prefix=f"{api_prefix}/feed", tags=["Feed"])
    app.include_router(
        applications.router, prefix=f"{api_prefix}/applications", tags=["Applications"]
    )
    app.include_router(
        community.router, prefix=f"{api_prefix}/community", tags=["Community"]
    )
    app.include_router(
        incoscore.router, prefix=f"{api_prefix}/incoscore", tags=["InCoScore"]
    )
    app.include_router(
        notifications.router,
        prefix=f"{api_prefix}/notifications",
        tags=["Notifications"],
    )
    app.include_router(admin.router, prefix=f"{api_prefix}/admin", tags=["Admin"])
    app.include_router(
        feature_flags.router, prefix=f"{api_prefix}/flags", tags=["Feature Flags"]
    )

    # ── Health Endpoints ──────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Overall health check")
    async def health_check():
        from app.core.redis import health_check as redis_health
        from sqlalchemy import text

        db_ok = False
        redis_ok = False

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            pass

        try:
            redis_ok = await redis_health()
        except Exception:
            pass

        overall = "healthy" if db_ok and redis_ok else "degraded"
        status_code = 200 if overall == "healthy" else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "status": overall,
                "version": settings.APP_VERSION,
                "database": "connected" if db_ok else "disconnected",
                "redis": "connected" if redis_ok else "disconnected",
            },
        )

    @app.get("/health/db", tags=["Health"], summary="Database health check")
    async def health_db():
        from sqlalchemy import text

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "connected"}
        except Exception as e:
            return JSONResponse(
                status_code=503, content={"status": "disconnected", "error": str(e)}
            )

    @app.get("/health/redis", tags=["Health"], summary="Redis health check")
    async def health_redis():
        from app.core.redis import health_check as redis_health

        ok = await redis_health()
        return JSONResponse(
            status_code=200 if ok else 503,
            content={"status": "connected" if ok else "disconnected"},
        )

    # ── WebSocket: Real-time Notification Push ────────────────
    from app.core.ws import manager as ws_manager
    from fastapi import WebSocket, WebSocketDisconnect

    @app.websocket("/ws/notifications/{user_id}")
    async def ws_notifications(websocket: WebSocket, user_id: str, token: str = ""):
        """
        Real-time notification push.
        Connect with: ws://host/ws/notifications/{user_id}?token=<JWT>
        """
        from app.core.security import verify_access_token

        try:
            payload = verify_access_token(token)
            if payload.get("sub") != user_id:
                await websocket.close(code=4003)
                return
        except Exception:
            await websocket.close(code=4001)
            return

        await ws_manager.connect(user_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(user_id, websocket)

    return app


app = create_application()
