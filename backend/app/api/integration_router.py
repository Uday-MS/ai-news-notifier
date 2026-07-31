"""Integration API router — orchestration endpoints for the full pipeline.

Provides endpoints to:
- Seed live AI sources (idempotent)
- Run collect-and-process in one call
- View system-wide integration status
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.event import CollectedEvent
from app.models.notification import Notification, NotificationStatus
from app.models.processed_event import ProcessedEvent
from app.models.user import User
from app.seeds.seed_sources import seed_sources
from app.services.collector_service import CollectorService
from app.services.pipeline.pipeline_service import PipelineService

router = APIRouter(prefix="/integration", tags=["integration"])


# ── Seed Sources ─────────────────────────────────────────────────────────


@router.post("/seed-sources", response_model=None)
async def seed_live_sources(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Register all live AI news sources. Idempotent — safe to call repeatedly."""
    result = await seed_sources(db)
    return success_response(
        data=result,
        message=f"Seeded {result['created']} new source(s), {result['skipped']} already existed.",
    )


# ── Collect and Process ──────────────────────────────────────────────────


@router.post("/collect-and-process", response_model=None)
async def collect_and_process(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run all active collectors, then process all unprocessed events.

    Chains: CollectorService.run_all_active() → PipelineService.process_all_unprocessed()
    """
    # Step 1: Collect
    collector_service = CollectorService(db)
    collector_results = await collector_service.run_all_active()

    total_fetched = sum(r.get("fetched", 0) for r in collector_results)
    total_emitted = sum(r.get("emitted", 0) for r in collector_results)
    total_duplicates = sum(r.get("duplicates", 0) for r in collector_results)
    collector_errors = sum(r.get("errors", 0) for r in collector_results)

    # Step 2: Process
    pipeline_service = PipelineService(db)
    pipeline_result = await pipeline_service.process_all_unprocessed()

    return success_response(
        data={
            "collection": {
                "sources_run": len(collector_results),
                "total_fetched": total_fetched,
                "total_emitted": total_emitted,
                "total_duplicates": total_duplicates,
                "errors": collector_errors,
                "details": collector_results,
            },
            "processing": pipeline_result,
        },
        message=(
            f"Collected {total_emitted} new event(s) from {len(collector_results)} source(s), "
            f"processed {pipeline_result.get('processed', 0)} event(s)."
        ),
    )


# ── Integration Status ──────────────────────────────────────────────────


@router.get("/status", response_model=None)
async def integration_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return system-wide counts across all modules."""
    # Collected events
    collected_result = await db.execute(
        select(func.count()).select_from(CollectedEvent)
    )
    total_collected = collected_result.scalar() or 0

    # Processed events
    processed_result = await db.execute(
        select(func.count()).select_from(ProcessedEvent)
    )
    total_processed = processed_result.scalar() or 0

    # Notifications
    notif_result = await db.execute(
        select(func.count()).select_from(Notification)
    )
    total_notifications = notif_result.scalar() or 0

    # Delivered notifications
    delivered_result = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.status == NotificationStatus.DELIVERED
        )
    )
    total_delivered = delivered_result.scalar() or 0

    return success_response(
        data={
            "collected_events": total_collected,
            "processed_events": total_processed,
            "unprocessed_events": total_collected - total_processed,
            "notifications": total_notifications,
            "delivered_notifications": total_delivered,
            "pipeline_coverage": round(
                (total_processed / total_collected * 100) if total_collected > 0 else 0, 1
            ),
        },
    )
