"""AI News Notifier — FastAPI Application Entry Point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.core.responses import error_response
from app.database.base import Base
from app.database.session import engine, async_session_factory
from app.seeds.seed_sources import seed_sources

# Import models so SQLAlchemy registers them
import app.models  # noqa: F401

# Import routers
from app.api.auth_router import router as auth_router
from app.api.health_router import router as health_router
from app.api.user_router import router as user_router
from app.api.collector_router import router as collector_router
from app.api.pipeline_router import router as pipeline_router
from app.api.feed_router import router as feed_router
from app.api.recommendation_router import router as recommendation_router
from app.api.notification_router import router as notification_router
from app.api.delivery_router import router as delivery_router
from app.api.integration_router import router as integration_router
from app.api.saved_router import router as saved_router

logger = get_logger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create tables, seed data, and start background pipeline."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-seed collector sources (idempotent)
    try:
        async with async_session_factory() as db:
            result = await seed_sources(db)
            await db.commit()
            logger.info(
                "Auto-seed complete",
                extra={"context": result},
            )
    except Exception as exc:
        logger.warning(
            "Auto-seed failed (non-fatal)",
            extra={"context": {"error": str(exc)}},
        )

    # Start background pipeline
    import asyncio
    pipeline_task = asyncio.create_task(_background_pipeline_loop())

    yield

    pipeline_task.cancel()
    await engine.dispose()


async def _background_pipeline_loop() -> None:
    """Run collect → process → notify every 30 minutes in the background."""
    import asyncio
    from app.services.collector_service import CollectorService
    from app.services.pipeline.pipeline_service import PipelineService
    from app.services.notification_service import NotificationService
    from app.models.user import User
    from sqlalchemy import select

    INTERVAL = 30 * 60  # 30 minutes

    # Wait 10s after startup before first run to let the server fully start
    await asyncio.sleep(10)

    while True:
        logger.info("Background pipeline: starting cycle")
        try:
            async with async_session_factory() as db:
                # Step 1: Collect
                collector_svc = CollectorService(db)
                results = await collector_svc.run_all_active()
                await db.commit()
                total_emitted = sum(r.get("emitted", 0) for r in results)
                total_errors = sum(r.get("errors", 0) for r in results)

            async with async_session_factory() as db:
                # Step 2: Process
                pipeline_svc = PipelineService(db)
                proc_result = await pipeline_svc.process_all_unprocessed()
                await db.commit()

            async with async_session_factory() as db:
                # Step 3: Notify
                stmt = select(User).where(User.onboarding_completed == True)  # noqa: E712
                user_result = await db.execute(stmt)
                users = list(user_result.scalars().all())
                notif_svc = NotificationService(db)
                total_notifs = 0
                for user in users:
                    gen = await notif_svc.generate_for_user(user, min_score=20.0, max_count=10)
                    total_notifs += gen.generated
                await db.commit()

            logger.info(
                "Background pipeline: cycle complete",
                extra={"context": {
                    "collected": total_emitted,
                    "collect_errors": total_errors,
                    "processed": proc_result.get("processed", 0),
                    "notifications": total_notifs,
                }},
            )
        except Exception as exc:
            logger.error(
                "Background pipeline: cycle failed",
                exc_info=exc,
            )

        await asyncio.sleep(INTERVAL)


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ──────────────────────────────────────────────────


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions with structured responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.code, exc.message),
    )


# ── Routers ──────────────────────────────────────────────────────────────

app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(user_router, prefix=settings.API_V1_PREFIX)
app.include_router(collector_router, prefix=settings.API_V1_PREFIX)
app.include_router(pipeline_router, prefix=settings.API_V1_PREFIX)
app.include_router(feed_router, prefix=settings.API_V1_PREFIX)
app.include_router(recommendation_router, prefix=settings.API_V1_PREFIX)
app.include_router(notification_router, prefix=settings.API_V1_PREFIX)
app.include_router(delivery_router, prefix=settings.API_V1_PREFIX)
app.include_router(integration_router, prefix=settings.API_V1_PREFIX)
app.include_router(saved_router, prefix=settings.API_V1_PREFIX)
