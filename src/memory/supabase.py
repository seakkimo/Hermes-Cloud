import logging
from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY, MEMORY_MAX_MESSAGES

logger = logging.getLogger(__name__)

_client: Client | None = None


def _get_client() -> Client | None:
    global _client
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def get_supabase_client() -> Client:
    """Public accessor for other modules."""
    c = _get_client()
    if not c:
        raise RuntimeError("Supabase not configured")
    return c


async def load_history(user_id: int) -> list[dict]:
    client = _get_client()
    if not client:
        return []
    try:
        result = (
            client.table("conversations")
            .select("role, content")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .limit(MEMORY_MAX_MESSAGES)
            .execute()
        )
        return [{"role": r["role"], "content": r["content"]} for r in result.data]
    except Exception as e:
        logger.error(f"Memory load error: {e}")
        return []


async def save_message(user_id: int, role: str, content: str) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.table("conversations").insert({
            "user_id": user_id,
            "role": role,
            "content": content,
        }).execute()
    except Exception as e:
        logger.error(f"Memory save error: {e}")


async def clear_history(user_id: int) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.table("conversations").delete().eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"Memory clear error: {e}")


async def count_history(user_id: int) -> int:
    """Return total number of messages stored for this user."""
    client = _get_client()
    if not client:
        return 0
    try:
        result = (
            client.table("conversations")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        return result.count or 0
    except Exception as e:
        logger.error(f"Memory count error: {e}")
        return 0


async def replace_history_with_summary(user_id: int, summary: str, keep_recent: int = 6) -> None:
    """Delete old messages, keep the latest `keep_recent`, prepend a summary system message."""
    client = _get_client()
    if not client:
        return
    try:
        # Get IDs of all messages ordered by time
        result = (
            client.table("conversations")
            .select("id")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
        all_ids = [r["id"] for r in (result.data or [])]
        # Keep only the last `keep_recent` IDs
        ids_to_delete = all_ids[:-keep_recent] if len(all_ids) > keep_recent else []
        if ids_to_delete:
            client.table("conversations").delete().in_("id", ids_to_delete).execute()
        # Insert summary as a system message at the top (oldest created_at trick: use insert)
        client.table("conversations").insert({
            "user_id": user_id,
            "role": "system",
            "content": f"[Conversation Summary]\n{summary}",
        }).execute()
    except Exception as e:
        logger.error(f"Memory replace error: {e}")


# ── Model registry (dynamic) ──────────────────────────────────────────────────

async def db_list_models() -> list[dict]:
    client = _get_client()
    if not client:
        return []
    result = client.table("models").select("*").order("priority").execute()
    return result.data or []


async def db_add_model(
    alias: str, model_id: str, provider: str,
    base_url: str, api_key: str, priority: int
) -> None:
    client = _get_client()
    if not client:
        return
    client.table("models").upsert({
        "alias": alias,
        "model_id": model_id,
        "provider": provider,
        "base_url": base_url,
        "api_key": api_key,
        "priority": priority,
        "is_active": True,
    }, on_conflict="alias").execute()


async def db_remove_model(alias: str) -> None:
    client = _get_client()
    if not client:
        return
    client.table("models").delete().eq("alias", alias).execute()


async def db_toggle_model(alias: str, is_active: bool) -> None:
    client = _get_client()
    if not client:
        return
    client.table("models").update({"is_active": is_active}).eq("alias", alias).execute()
