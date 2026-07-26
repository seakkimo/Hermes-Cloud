"""Email tool — send via SMTP, read via IMAP."""
import logging
import smtplib
import imaplib
import email as email_lib
from email.mime.text import MIMEText
from email.header import decode_header
from config.settings import (
    EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_HOST, SMTP_PORT,
    IMAP_HOST, IMAP_PORT,
)

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via SMTP."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "❌ Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in environment."
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [to], msg.as_string())
        return f"✅ Email sent to {to}: {subject}"
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        return f"❌ Failed to send email: {e}"


async def read_emails(count: int = 5, folder: str = "INBOX") -> str:
    """Read the latest N emails from IMAP inbox."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "❌ Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in environment."
    try:
        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=15) as imap:
            imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            imap.select(folder)
            _, msg_ids = imap.search(None, "ALL")
            ids = msg_ids[0].split()
            latest = ids[-count:] if len(ids) >= count else ids
            lines = [f"📬 Latest {len(latest)} emails from {folder}:"]
            for mid in reversed(latest):
                _, data = imap.fetch(mid, "(RFC822)")
                msg = email_lib.message_from_bytes(data[0][1])
                subject = _decode_header(msg.get("Subject", "(no subject)"))
                sender = _decode_header(msg.get("From", ""))
                date = msg.get("Date", "")[:16]
                lines.append(f"• [{date}] {sender} — {subject}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"IMAP error: {e}")
        return f"❌ Failed to read emails: {e}"


def _decode_header(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)
