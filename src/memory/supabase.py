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
