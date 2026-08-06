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
MAX_BODY_CHARS = 3000


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
    """Read the latest N emails, with index numbers for use with /email read."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "❌ Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in environment."
    try:
        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=15) as imap:
            imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            imap.select(folder)
            _, msg_ids = imap.search(None, "ALL")
            ids = msg_ids[0].split()
            latest = ids[-count:] if len(ids) >= count else ids
            lines = [f"📬 Latest {len(latest)} emails (use `/email read <no>` to read body):\n"]
            for i, mid in enumerate(reversed(latest), start=1):
                _, data = imap.fetch(mid, "(RFC822)")
                msg = email_lib.message_from_bytes(data[0][1])
                subject = _decode_str(msg.get("Subject", "(no subject)"))
                sender = _decode_str(msg.get("From", ""))
                date = msg.get("Date", "")[:16]
                lines.append(f"[{i}] {date}\n    From: {sender}\n    Subject: {subject}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"IMAP error: {e}")
        return f"❌ Failed to read emails: {e}"


async def read_email_body(index: int = 1, count: int = 5, folder: str = "INBOX") -> str:
    """Read the full body of email at position `index` (1=latest) from inbox."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "❌ Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in environment."
    try:
        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=15) as imap:
            imap.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            imap.select(folder)
            _, msg_ids = imap.search(None, "ALL")
            ids = msg_ids[0].split()
            latest = ids[-count:] if len(ids) >= count else ids
            latest_reversed = list(reversed(latest))

            if index < 1 or index > len(latest_reversed):
                return f"❌ Index {index} out of range. Use `/email inbox` to see available emails (1~{len(latest_reversed)})."

            mid = latest_reversed[index - 1]
            _, data = imap.fetch(mid, "(RFC822)")
            msg = email_lib.message_from_bytes(data[0][1])

            subject = _decode_str(msg.get("Subject", "(no subject)"))
            sender = _decode_str(msg.get("From", ""))
            date = msg.get("Date", "")[:25]
            body = _extract_body(msg)

            if len(body) > MAX_BODY_CHARS:
                body = body[:MAX_BODY_CHARS] + "\n\n…（內文過長，已截斷）"

            return (
                f"📧 *Email [{index}]*\n"
                f"From: {sender}\n"
                f"Date: {date}\n"
                f"Subject: {subject}\n"
                f"{'─' * 30}\n"
                f"{body}"
            )
    except Exception as e:
        logger.error(f"IMAP read body error: {e}")
        return f"❌ Failed to read email body: {e}"


def _extract_body(msg) -> str:
    """Extract plain text body from email message."""
    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                charset = part.get_content_charset() or "utf-8"
                body_parts.append(part.get_payload(decode=True).decode(charset, errors="replace"))
    else:
        charset = msg.get_content_charset() or "utf-8"
        body_parts.append(msg.get_payload(decode=True).decode(charset, errors="replace"))
    return "\n".join(body_parts).strip() or "(no text content)"


def _decode_str(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)
