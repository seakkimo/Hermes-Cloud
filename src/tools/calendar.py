"""Calendar tool — stores events in Supabase `calendar` table."""
import logging
from datetime import datetime, timezone, timedelta
from src.memory.supabase import get_supabase_client

logger = logging.getLogger(__name__)
TZ_TAIPEI = timezone(timedelta(hours=8))


def _client():
    return get_supabase_client()


async def add_event(title: str, start: str, end: str = "", description: str = "", user_id: int = 0) -> str:
    """Add a calendar event. start/end format: YYYY-MM-DD HH:MM or YYYY-MM-DD"""
    try:
        _client().table("calendar").insert({
            "user_id": user_id,
            "title": title,
            "start_time": start,
            "end_time": end or start,
            "description": description,
        }).execute()
        return f"✅ Event added: **{title}** at {start}"
    except Exception as e:
        logger.error(f"Calendar add error: {e}")
        return f"❌ Failed to add event: {e}"


async def list_events(days: int = 7, user_id: int = 0) -> str:
    """List upcoming events within the next N days."""
    try:
        now = datetime.now(TZ_TAIPEI)
        until = now + timedelta(days=days)
        result = (
            _client().table("calendar")
            .select("title, start_time, end_time, description")
            .eq("user_id", user_id)
            .gte("start_time", now.strftime("%Y-%m-%d"))
            .lte("start_time", until.strftime("%Y-%m-%d"))
            .order("start_time")
            .execute()
        )
        events = result.data or []
        if not events:
            return f"No events in the next {days} days."
        lines = [f"📅 Upcoming events (next {days} days):"]
        for e in events:
            desc = f" — {e['description']}" if e.get("description") else ""
            lines.append(f"• {e['start_time']} | {e['title']}{desc}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Calendar list error: {e}")
        return f"❌ Failed to list events: {e}"


async def delete_event(title: str, user_id: int = 0) -> str:
    """Delete an event by title (deletes first match)."""
    try:
        result = (
            _client().table("calendar")
            .select("id, title")
            .eq("user_id", user_id)
            .ilike("title", f"%{title}%")
            .limit(1)
            .execute()
        )
        if not result.data:
            return f"❌ No event found matching '{title}'"
        event_id = result.data[0]["id"]
        _client().table("calendar").delete().eq("id", event_id).execute()
        return f"🗑 Deleted event: {result.data[0]['title']}"
    except Exception as e:
        logger.error(f"Calendar delete error: {e}")
        return f"❌ Failed to delete event: {e}"


async def get_due_reminders(hours_ahead: int = 24) -> list[dict]:
    """
    Return all events starting within the next `hours_ahead` hours, across ALL users.
    Each item: {user_id, title, start_time, description}
    """
    try:
        now = datetime.now(TZ_TAIPEI)
        until = now + timedelta(hours=hours_ahead)
        result = (
            _client().table("calendar")
            .select("user_id, title, start_time, description")
            .gte("start_time", now.strftime("%Y-%m-%d %H:%M"))
            .lte("start_time", until.strftime("%Y-%m-%d %H:%M"))
            .order("start_time")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Calendar reminder query error: {e}")
        return []
