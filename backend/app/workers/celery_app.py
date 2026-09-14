"""
Celery application configuration.
"""
import sys

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "bharatai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.scrape_tasks",
        "app.workers.ai_tasks",
        "app.workers.notification_tasks",
    ],
)

celery_app.conf.update(
    worker_pool="solo" if sys.platform == "win32" else "prefork",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.scrape_tasks.*": {"queue": "scraping"},
        "app.workers.ai_tasks.*": {"queue": "ai"},
        "app.workers.notification_tasks.*": {"queue": "notifications"},
    },
    task_default_queue="default",
    beat_schedule={
        "ingest-live-opportunities-production": {
            "task": "app.workers.scrape_tasks.ingest_live_opportunities_task",
            "schedule": crontab(
                minute=0, hour="0,6,12,18"
            ),  # Runs 4x daily at 00:00, 06:00, 12:00, 18:00 IST
            "options": {"queue": "scraping"},
        },
        "scrape-all-sources": {
            "task": "app.workers.scrape_tasks.scrape_all_sources",
            "schedule": crontab(minute=f"*/{settings.CELERY_SCRAPE_INTERVAL_MINUTES}"),
            "options": {"queue": "scraping"},
        },
        "deadline-reminders-7d": {
            "task": "app.workers.notification_tasks.send_deadline_reminders",
            "schedule": crontab(hour=8, minute=0),  # 8AM IST daily
            "args": [7],
            "options": {"queue": "notifications"},
        },
        "deadline-reminders-1d": {
            "task": "app.workers.notification_tasks.send_deadline_reminders",
            "schedule": crontab(hour=8, minute=0),
            "args": [1],
            "options": {"queue": "notifications"},
        },
        "rebuild-faiss-index": {
            "task": "app.workers.ai_tasks.rebuild_faiss_index",
            "schedule": crontab(hour=2, minute=0),  # 2AM IST daily
            "options": {"queue": "ai"},
        },
        "check-url-health": {
            "task": "app.workers.scrape_tasks.check_url_health",
            "schedule": crontab(
                hour=3, minute=0, day_of_week=0
            ),  # 3AM IST every Sunday
            "options": {"queue": "scraping"},
        },
    },
)
