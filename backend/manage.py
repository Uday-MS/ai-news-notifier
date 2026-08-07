#!/usr/bin/env python
"""AI News Notifier — Management CLI.

Usage:
    python manage.py seed              # Seed collector sources
    python manage.py collect           # Run all active collectors
    python manage.py process           # Process all unprocessed events
    python manage.py notify [email]    # Generate notifications (all users or specific)
    python manage.py full-pipeline     # Seed + Collect + Process + Notify (all users)
    python manage.py status            # Show database status
"""

from __future__ import annotations

import asyncio
import sys

from app.database.session import async_session_factory
from app.database.base import Base
from app.database.session import engine


async def cmd_seed() -> None:
    """Seed collector sources."""
    from app.seeds.seed_sources import seed_sources

    async with async_session_factory() as db:
        result = await seed_sources(db)
        await db.commit()
    print(f"✓ Seeded {result['created']} source(s), {result['skipped']} skipped")
    print(f"  Total: {result['total']} sources")


async def cmd_collect() -> None:
    """Run all active collectors."""
    from app.services.collector_service import CollectorService

    async with async_session_factory() as db:
        service = CollectorService(db)
        results = await service.run_all_active()
        await db.commit()

    total_emitted = 0
    total_errors = 0
    for r in results:
        name = r.get("source_name", "unknown")
        emitted = r.get("emitted", 0)
        errors = r.get("errors", 0)
        total_emitted += emitted
        total_errors += errors
        status = "✓" if errors == 0 else "✗"
        print(f"  {status} {name}: {emitted} articles" + (f" ({errors} errors)" if errors else ""))

    print(f"\n✓ Collected {total_emitted} article(s) from {len(results)} source(s)")
    if total_errors:
        print(f"  ⚠ {total_errors} error(s) — some sources may have changed URLs")


async def cmd_process() -> None:
    """Process all unprocessed events."""
    from app.services.pipeline.pipeline_service import PipelineService

    async with async_session_factory() as db:
        service = PipelineService(db)
        result = await service.process_all_unprocessed()
        await db.commit()

    print(f"✓ Processed {result.get('processed', 0)} event(s)")
    print(f"  Failed: {result.get('failed', 0)}")
    print(f"  Skipped: {result.get('skipped', 0)}")


async def cmd_notify(email: str | None = None) -> None:
    """Generate notifications for users."""
    from sqlalchemy import select
    from app.models.user import User
    from app.services.notification_service import NotificationService

    async with async_session_factory() as db:
        if email:
            result = await db.execute(select(User).where(User.email == email))
            users = [result.scalar_one_or_none()]
            if users[0] is None:
                print(f"✗ User not found: {email}")
                return
        else:
            result = await db.execute(select(User).where(User.onboarding_completed == True))  # noqa: E712
            users = list(result.scalars().all())

        if not users:
            print("✗ No users found")
            return

        service = NotificationService(db)
        total_generated = 0
        for user in users:
            gen_result = await service.generate_for_user(
                user, min_score=20.0, max_count=15
            )
            total_generated += gen_result.generated
            print(f"  ✓ {user.email}: {gen_result.generated} notification(s)")

        await db.commit()

    print(f"\n✓ Generated {total_generated} notification(s) for {len(users)} user(s)")


async def cmd_status() -> None:
    """Show database status."""
    import sqlite3

    conn = sqlite3.connect("aindb.db")
    cur = conn.cursor()

    tables = [
        "users", "user_interests", "collector_sources",
        "collected_events", "processed_events", "notifications",
        "saved_articles",
    ]

    print("=== Database Status ===\n")
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            emoji = "✓" if count > 0 else "○"
            print(f"  {emoji} {table}: {count} rows")
        except Exception:
            print(f"  ✗ {table}: table not found")

    conn.close()


async def cmd_full_pipeline() -> None:
    """Run the complete pipeline: seed → collect → process → notify."""
    print("═══ AI News Notifier — Full Pipeline ═══\n")

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Step 1/4: Seeding sources...")
    await cmd_seed()

    print("\nStep 2/4: Running collectors...")
    await cmd_collect()

    print("\nStep 3/4: Processing events...")
    await cmd_process()

    print("\nStep 4/4: Generating notifications...")
    await cmd_notify()

    print("\n═══ Pipeline Complete ═══")
    await cmd_status()


COMMANDS = {
    "seed": cmd_seed,
    "collect": cmd_collect,
    "process": cmd_process,
    "notify": cmd_notify,
    "full-pipeline": cmd_full_pipeline,
    "status": cmd_status,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "notify" and len(sys.argv) > 2:
        asyncio.run(cmd_notify(sys.argv[2]))
    else:
        asyncio.run(COMMANDS[command]())


if __name__ == "__main__":
    main()
