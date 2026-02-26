import json
import uuid
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.models.opportunity import MonitoredSource, ScrapeDeadLetter
from app.workers.scrape_tasks import _log_dead_letter
from sqlalchemy import select


def test_dead_letter_persistence_path_writes_db_record(run_async):
    source_id = uuid.uuid4()

    async def _run():
        async with AsyncSessionLocal() as db:
            source = MonitoredSource(
                id=source_id,
                name="DLQ Test Source",
                url=f"https://example.com/source/{source_id.hex}",
                type="static",
                interval_minutes=30,
                active=True,
            )
            db.add(source)
            await db.commit()

        payload = {
            "status": "failure",
            "source_id": str(source_id),
            "error": "Timeout while fetching source",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        dead_letter_id = await _log_dead_letter(
            task_name="app.workers.scrape_tasks.scrape_single_source",
            source_id=str(source_id),
            payload=payload,
            error_message="Timeout while fetching source",
            retry_count=3,
        )

        async with AsyncSessionLocal() as db:
            record = (
                await db.execute(
                    select(ScrapeDeadLetter).where(
                        ScrapeDeadLetter.id == uuid.UUID(dead_letter_id)
                    )
                )
            ).scalar_one_or_none()

        assert record is not None
        assert record.task_name == "app.workers.scrape_tasks.scrape_single_source"
        assert record.source_id == source_id
        assert record.retry_count == 3
        assert "Timeout while fetching source" in record.error_message
        assert json.loads(record.payload_json)["status"] == "failure"

    run_async(_run())
