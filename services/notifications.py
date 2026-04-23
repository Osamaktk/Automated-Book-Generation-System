import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx


logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_TO = os.environ.get("SMTP_TO", "")
TEAMS_WEBHOOK = os.environ.get("TEAMS_WEBHOOK", "")

EVENT_LABELS = {
    "outline_ready": "Outline Ready for Review",
    "chapter_ready": "Chapter Ready for Review",
    "book_complete": "Book Compilation Complete",
}


def send_email(subject: str, body: str) -> None:
    """
    Send a plain-text email via SMTP TLS.
    Silently skips when SMTP configuration is incomplete.
    Logs and swallows all exceptions.
    """
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_TO]):
        logger.debug("SMTP notification skipped because configuration is incomplete")
        return

    try:
        message = MIMEMultipart()
        message["From"] = SMTP_USER
        message["To"] = SMTP_TO
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(
                SMTP_USER,
                [email.strip() for email in SMTP_TO.split(",") if email.strip()],
                message.as_string(),
            )
    except Exception as exc:
        logger.error("Email notification failed: %s", exc, exc_info=True)


def send_teams(title: str, body: str) -> None:
    """
    Post a message card to Microsoft Teams via webhook.
    Silently skips when the webhook is not configured.
    Logs and swallows all exceptions.
    """
    if not TEAMS_WEBHOOK:
        logger.debug("Teams notification skipped because webhook is not configured")
        return

    try:
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "themeColor": "D4A843",
            "title": title,
            "text": body,
        }
        with httpx.Client(timeout=10.0) as client:
            client.post(TEAMS_WEBHOOK, json=payload).raise_for_status()
    except Exception as exc:
        logger.error("Teams notification failed: %s", exc, exc_info=True)


def notify(event: str, book_title: str, detail: str = "") -> None:
    """
    Dispatch a notification to all configured channels.

    Email and Teams are attempted independently so a failure in one
    channel never prevents the other from firing.
    """
    label = EVENT_LABELS.get(event, event)
    subject = f"{label} - {book_title}"
    body = f"Book: {book_title}"
    if detail:
        body = f"{body}\n\n{detail}"

    send_email(subject, body)
    send_teams(label, body)
