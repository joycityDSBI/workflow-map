"""Teams channel notification via SMTP relay.

Teams channel email: configured in settings.TEAMS_NOTIFICATION_EMAIL
"""

from __future__ import annotations

import logging
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def notify_review_pending(
    item_name: str,
    item_type: str,
    review_url: str,
) -> None:
    """Send email to Teams channel when an item enters PENDING_REVIEW."""
    if not settings.TEAMS_NOTIFICATION_EMAIL:
        return

    subject = f"[워크플로우 맵] 검수 요청: {item_name}"
    body = f"""새로운 {item_type} 항목이 검수를 기다리고 있습니다.

항목명: {item_name}
유형: {item_type}
검수 링크: {review_url}

워크플로우 맵 검수 시스템에서 발송된 알림입니다.
"""
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = settings.TEAMS_NOTIFICATION_EMAIL

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=False,
            start_tls=False,
        )
    except Exception as exc:
        logger.warning("Teams notification failed: %s", exc)


async def notify_approved(item_name: str, item_type: str) -> None:
    """Notify when item is approved and published."""
    # Future: notify submitter
    pass
