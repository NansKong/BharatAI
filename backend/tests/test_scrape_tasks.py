import uuid

from app.workers import scrape_tasks


def test_scrape_all_sources_queues_every_active_source(monkeypatch):
    source_ids = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
    queued_source_ids: list[str] = []

    async def fake_get_active_source_ids():
        return source_ids

    async def fake_run_with_db_cleanup(coro):
        return await coro

    class DummyScrapeSingleSourceTask:
        @staticmethod
        def delay(source_id: str):
            queued_source_ids.append(source_id)

    monkeypatch.setattr(
        scrape_tasks, "_get_active_source_ids", fake_get_active_source_ids
    )
    monkeypatch.setattr(scrape_tasks, "_run_with_db_cleanup", fake_run_with_db_cleanup)
    monkeypatch.setattr(
        scrape_tasks, "scrape_single_source", DummyScrapeSingleSourceTask()
    )

    result = scrape_tasks.scrape_all_sources.run()

    assert result == {"queued_sources": len(source_ids)}
    assert queued_source_ids == source_ids
