"""Todo tool — stores tasks in Supabase `todos` table."""
import logging
from src.memory.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def _client():
    return get_supabase_client()


async def add_todo(title: str, user_id: int = 0) -> str:
    try:
        _client().table("todos").insert({
            "user_id": user_id,
            "title": title,
            "done": False,
        }).execute()
        return f"✅ Todo added: **{title}**"
    except Exception as e:
        logger.error(f"Todo add error: {e}")
        return f"❌ Failed to add todo: {e}"


async def list_todos(user_id: int = 0, show_done: bool = False) -> str:
    try:
        q = _client().table("todos").select("id, title, done, created_at").eq("user_id", user_id)
        if not show_done:
            q = q.eq("done", False)
        result = q.order("created_at").execute()
        items = result.data or []
        if not items:
            return "📭 No pending todos." if not show_done else "📭 No todos found."
        lines = ["📝 Todo list:"]
        for i, item in enumerate(items, 1):
            mark = "✅" if item["done"] else "⬜"
            lines.append(f"{i}. {mark} {item['title']}  `#{item['id']}`")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Todo list error: {e}")
        return f"❌ Failed to list todos: {e}"


async def complete_todo(title: str, user_id: int = 0) -> str:
    try:
        result = (
            _client().table("todos")
            .select("id, title")
            .eq("user_id", user_id)
            .eq("done", False)
            .ilike("title", f"%{title}%")
            .limit(1)
            .execute()
        )
        if not result.data:
            return f"❌ No pending todo matching '{title}'"
        row = result.data[0]
        _client().table("todos").update({"done": True}).eq("id", row["id"]).execute()
        return f"✅ Marked done: **{row['title']}**"
    except Exception as e:
        logger.error(f"Todo complete error: {e}")
        return f"❌ Failed to complete todo: {e}"


async def delete_todo(title: str, user_id: int = 0) -> str:
    try:
        result = (
            _client().table("todos")
            .select("id, title")
            .eq("user_id", user_id)
            .ilike("title", f"%{title}%")
            .limit(1)
            .execute()
        )
        if not result.data:
            return f"❌ No todo found matching '{title}'"
        row = result.data[0]
        _client().table("todos").delete().eq("id", row["id"]).execute()
        return f"🗑 Deleted todo: **{row['title']}**"
    except Exception as e:
        logger.error(f"Todo delete error: {e}")
        return f"❌ Failed to delete todo: {e}"
