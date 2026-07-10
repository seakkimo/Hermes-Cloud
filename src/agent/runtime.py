import logging
from src.llm.openrouter import chat
from src.agent.session import get_model, is_auto
from src.memory.supabase import load_history, save_message
from src.tools.browser import search, fetch_page

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Hermes, a personal AI assistant. "
    "Be concise, helpful, and honest."
)

SEARCH_DECISION_PROMPT = (
    "判斷以下問題是否需要搜尋網路才能回答（即時資訊、特定網站、最新消息、不確定的事實）。"
    "只回答 YES 或 NO，不要其他文字。"
)


async def _needs_search(user_message: str) -> bool:
    messages = [
        {"role": "system", "content": SEARCH_DECISION_PROMPT},
        {"role": "user", "content": user_message},
    ]
    try:
        result = await chat(messages)
        return result.strip().upper().startswith("YES")
    except Exception:
        return False


async def _run_search(query: str) -> str:
    results = search(query)
    if not results:
        return "（搜尋無結果）"
    context = "\n\n".join(
        f"標題：{r['title']}\n網址：{r['url']}\n摘要：{r['snippet']}"
        for r in results
    )
    return context


async def run(user_message: str, user_id: int = 0, force_browse: str = "") -> str:
    history = await load_history(user_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history

    # Force browse mode: /browse <url>
    if force_browse:
        page_content = await fetch_page(force_browse)
        messages.append({
            "role": "user",
            "content": f"以下是網頁內容：\n\n{page_content}\n\n{user_message}",
        })
    else:
        # Auto-detect if search is needed
        needs_web = await _needs_search(user_message)
        if needs_web:
            logger.info(f"Auto search triggered for: {user_message}")
            search_context = await _run_search(user_message)
            messages.append({
                "role": "user",
                "content": f"以下是網路搜尋結果，請根據這些資料回答問題：\n\n{search_context}\n\n問題：{user_message}",
            })
        else:
            messages.append({"role": "user", "content": user_message})

    if is_auto(user_id):
        reply = await chat(messages)
    else:
        model = get_model(user_id)
        reply = await chat(messages, model=model, fallback=False)

    await save_message(user_id, "user", user_message)
    await save_message(user_id, "assistant", reply)

    return reply
