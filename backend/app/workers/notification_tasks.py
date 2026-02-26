"""
Celery notification tasks — triggered by application events.
All DB interactions use asyncio.get_event_loop().run_until_complete() so they
can run in a synchronous Celery worker process.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _is_email_enabled_for(profile, notification_type: str) -> bool:
    """Return True if user has not explicitly disabled this notification type."""
    if profile is None:
        return False
    prefs_raw = getattr(profile, "email_prefs", None)
    if not prefs_raw:
        return True  # default: all enabled
    try:
        prefs = json.loads(prefs_raw)
        return bool(prefs.get(notification_type, True))
    except Exception:
        return True


async def _create_notification(
    db, user_id, notif_type: str, title: str, message: str, payload: dict | None = None
):
    """Insert a Notification row and push via WebSocket."""
    from app.models.incoscore import Notification

    n = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
        payload_json=json.dumps(payload or {}),
    )
    db.add(n)
    await db.flush()

    # Best-effort WebSocket push
    try:
        from app.core.ws import manager

        await manager.send_to_user(
            str(user_id),
            {
                "type": "notification",
                "id": str(n.id),
                "title": title,
                "message": message,
            },
        )
    except Exception:
        pass

    return n


@celery_app.task(name="notifications.opportunity_match", bind=True, max_retries=3)
def send_opportunity_match_notification(self, user_id: str, opportunity_id: str):
    """Create in-app notification and send email for a matched opportunity."""

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.opportunity import Opportunity
        from app.models.user import Profile, User
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            user = (
                await db.execute(select(User).where(User.id == user_id))
            ).scalar_one_or_none()
            profile = (
                await db.execute(select(Profile).where(Profile.user_id == user_id))
            ).scalar_one_or_none()
            opp = (
                await db.execute(
                    select(Opportunity).where(Opportunity.id == opportunity_id)
                )
            ).scalar_one_or_none()
            if not user or not opp:
                return {"status": "skip", "reason": "user or opportunity not found"}

            await _create_notification(
                db,
                user_id=user.id,
                notif_type="opportunity_match",
                title="New opportunity match",
                message=f"We found a new opportunity for you: {opp.title}",
                payload={"opportunity_id": opportunity_id},
            )

            if _is_email_enabled_for(profile, "opportunity_match"):
                from app.services.email import send_opportunity_match_email

                send_opportunity_match_email(
                    to=user.email,
                    user_name=user.name,
                    opp_title=opp.title,
                    opp_link=opp.application_link or opp.source_url or "",
                )

            await db.commit()
            return {"status": "ok"}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(name="notifications.deadline_reminder", bind=True, max_retries=3)
def send_deadline_reminder(self, opportunity_id: str, days_remaining: int):
    """Notify all applicants about an approaching deadline."""

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.application import Application
        from app.models.opportunity import Opportunity
        from app.models.user import Profile, User
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            opp = (
                await db.execute(
                    select(Opportunity).where(Opportunity.id == opportunity_id)
                )
            ).scalar_one_or_none()
            if not opp:
                return {"status": "skip"}

            applications = (
                (
                    await db.execute(
                        select(Application).where(
                            Application.opportunity_id == opportunity_id
                        )
                    )
                )
                .scalars()
                .all()
            )

            notified = 0
            for app in applications:
                user = (
                    await db.execute(select(User).where(User.id == app.user_id))
                ).scalar_one_or_none()
                profile = (
                    await db.execute(
                        select(Profile).where(Profile.user_id == app.user_id)
                    )
                ).scalar_one_or_none()
                if not user:
                    continue

                await _create_notification(
                    db,
                    user_id=user.id,
                    notif_type="deadline_reminder",
                    title=f"Deadline in {days_remaining} day(s): {opp.title}",
                    message=f"Your application deadline is approaching ({days_remaining}d left).",
                    payload={
                        "opportunity_id": opportunity_id,
                        "days_remaining": days_remaining,
                    },
                )

                if _is_email_enabled_for(profile, "deadline_reminder"):
                    from app.services.email import send_deadline_reminder_email

                    send_deadline_reminder_email(
                        to=user.email,
                        user_name=user.name,
                        opp_title=opp.title,
                        days_remaining=days_remaining,
                    )
                notified += 1

            await db.commit()
            return {"status": "ok", "notified": notified}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(name="notifications.achievement_result", bind=True, max_retries=3)
def notify_achievement_result(self, achievement_id: str):
    """Email + in-app notification when an achievement is verified or rejected."""

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.application import Achievement
        from app.models.user import Profile, User
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            ach = (
                await db.execute(
                    select(Achievement).where(Achievement.id == achievement_id)
                )
            ).scalar_one_or_none()
            if not ach:
                return {"status": "skip"}

            user = (
                await db.execute(select(User).where(User.id == ach.user_id))
            ).scalar_one_or_none()
            profile = (
                await db.execute(select(Profile).where(Profile.user_id == ach.user_id))
            ).scalar_one_or_none()
            if not user:
                return {"status": "skip"}

            status_word = "verified" if ach.verified else "not verified"
            await _create_notification(
                db,
                user_id=user.id,
                notif_type="achievement_verified",
                title=f"Achievement {status_word}: {ach.title}",
                message=f"Your achievement '{ach.title}' has been {status_word}.",
                payload={"achievement_id": achievement_id, "verified": ach.verified},
            )

            if _is_email_enabled_for(profile, "achievement_verified"):
                from app.services.email import send_achievement_result_email

                send_achievement_result_email(
                    to=user.email,
                    user_name=user.name,
                    achievement_title=ach.title,
                    verified=ach.verified,
                    reason=getattr(ach, "rejection_reason", None),
                )

            await db.commit()
            return {"status": "ok", "verified": ach.verified}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(name="notifications.score_change", bind=True, max_retries=3)
def notify_score_change(self, user_id: str, old_score: float, new_score: float):
    """In-app notification when InCoScore changes by > 50 pts."""
    if abs(new_score - old_score) <= 50:
        return {"status": "skip", "reason": "delta <= 50"}

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.user import User
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            user = (
                await db.execute(select(User).where(User.id == user_id))
            ).scalar_one_or_none()
            if not user:
                return {"status": "skip"}

            delta = new_score - old_score
            direction = "increased" if delta > 0 else "decreased"
            await _create_notification(
                db,
                user_id=user.id,
                notif_type="score_change",
                title=f"InCoScore {direction}!",
                message=f"Your InCoScore {direction} by {abs(delta):.0f} pts: {old_score:.0f} → {new_score:.0f}",
                payload={
                    "old_score": old_score,
                    "new_score": new_score,
                    "delta": delta,
                },
            )

            await db.commit()
            return {"status": "ok", "delta": delta}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(name="notifications.check_deadlines", bind=True)
def check_deadlines(self):
    """
    Celery Beat task — runs daily at 8 AM IST.
    Scans opportunities with deadlines 1 or 7 days away and queues reminders.
    """

    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.opportunity import Opportunity
        from sqlalchemy import and_, select

        now = datetime.now(timezone.utc)
        targets = {1: now + timedelta(days=1), 7: now + timedelta(days=7)}
        queued = 0

        async with AsyncSessionLocal() as db:
            for days, target_dt in targets.items():
                window_start = target_dt.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                window_end = window_start + timedelta(days=1)
                opps = (
                    (
                        await db.execute(
                            select(Opportunity).where(
                                and_(
                                    Opportunity.deadline >= window_start,
                                    Opportunity.deadline < window_end,
                                )
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                for opp in opps:
                    send_deadline_reminder.delay(str(opp.id), days)
                    queued += 1

        return {"status": "ok", "queued": queued}

    return asyncio.get_event_loop().run_until_complete(_run())
