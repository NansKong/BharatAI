"""
Email service — wraps smtplib with Jinja2 template rendering.
When EMAIL_ENABLED=false (default in tests) emails are only logged, no SMTP needed.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    """Minimal Jinja2 rendering (falls back to plain f-string if Jinja2 not installed)."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        tmpl = env.get_template(template_name)
        return tmpl.render(**context)
    except Exception:
        # Plain text fallback
        path = _TEMPLATES_DIR / template_name
        if path.exists():
            html = path.read_text(encoding="utf-8")
            for key, val in context.items():
                html = html.replace(f"{{{{ {key} }}}}", str(val))
            return html
        return f"Notification: {context}"


def send_email(
    to: str,
    subject: str,
    template: str,
    context: dict[str, Any],
    *,
    email_enabled: bool | None = None,
) -> bool:
    """
    Render `template` with `context` and send to `to`.
    Returns True if sent, False if skipped/disabled.

    Reads config from app.core.config.settings when available.
    Falls back to env-var inspection for test isolation.
    """
    # Resolve enabled flag
    if email_enabled is None:
        try:
            from app.core.config import settings

            email_enabled = getattr(settings, "EMAIL_ENABLED", False)
        except Exception:
            email_enabled = False

    html_body = _render_template(template, context)

    if not email_enabled:
        logger.info(
            "EMAIL SKIPPED (disabled) to=%s subject=%s body_len=%d",
            to,
            subject,
            len(html_body),
        )
        return False

    try:
        from app.core.config import settings

        smtp_host: str = getattr(settings, "SMTP_HOST", "localhost")
        smtp_port: int = int(getattr(settings, "SMTP_PORT", 587))
        smtp_user: str = getattr(settings, "SMTP_USER", "")
        smtp_pass: str = getattr(settings, "SMTP_PASS", "")
        from_addr: str = getattr(settings, "EMAIL_FROM", "noreply@bharatai.in")
    except Exception:
        logger.error("Email config unavailable — skipping send")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=ctx)
            if smtp_user:
                server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to], msg.as_string())
        logger.info("Email sent to=%s subject=%s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to=%s: %s", to, exc, exc_info=True)
        return False


# ---------------------------------------------------------------------------
# Typed helpers (used by Celery tasks)
# ---------------------------------------------------------------------------


def send_opportunity_match_email(
    to: str, user_name: str, opp_title: str, opp_link: str
) -> bool:
    return send_email(
        to=to,
        subject=f"New opportunity match: {opp_title}",
        template="opportunity_match.html",
        context={"user_name": user_name, "opp_title": opp_title, "opp_link": opp_link},
    )


def send_deadline_reminder_email(
    to: str, user_name: str, opp_title: str, days_remaining: int
) -> bool:
    urgency = "Urgent" if days_remaining <= 1 else "Reminder"
    return send_email(
        to=to,
        subject=f"[{urgency}] Deadline in {days_remaining}d: {opp_title}",
        template="deadline_reminder.html",
        context={
            "user_name": user_name,
            "opp_title": opp_title,
            "days_remaining": days_remaining,
        },
    )


def send_achievement_result_email(
    to: str,
    user_name: str,
    achievement_title: str,
    verified: bool,
    reason: str | None = None,
) -> bool:
    status_word = "Verified ✅" if verified else "Rejected ❌"
    return send_email(
        to=to,
        subject=f"Achievement {status_word}: {achievement_title}",
        template="achievement_verified.html",
        context={
            "user_name": user_name,
            "achievement_title": achievement_title,
            "verified": verified,
            "reason": reason or "",
        },
    )


def send_score_change_email(
    to: str, user_name: str, old_score: float, new_score: float
) -> bool:
    return send_email(
        to=to,
        subject=f"Your InCoScore changed: {old_score:.0f} → {new_score:.0f}",
        template="score_change.html",
        context={
            "user_name": user_name,
            "old_score": old_score,
            "new_score": new_score,
            "delta": new_score - old_score,
        },
    )
