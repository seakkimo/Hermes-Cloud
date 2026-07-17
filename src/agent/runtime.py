import logging
from src.llm.llm import chat
from src.agent.session import get_model, is_auto, get_search_engine
from src.memory.supabase import load_history, save_message
from src.tools.browser import fetch_page

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Hermes, a personal AI assistant. "
    "Be concise, helpful, and honest."
)

SEARCH_KEYWORDS = [
    "今天", "今日", "最新", "最近", "現在", "目前",
    "新聞", "消息", "動態", "資訊",
    "搜尋", "查一下", "幫我找", "幫我查", "查詢",
    "latest", "recent", "today", "news", "search", "find",
]


def _needs_search(user_message: str) -> bool:
    msg_lower = user_message.lower()
    return any(kw in msg_lower for kw in SEARCH_KEYWORDS)


async def _run_search(query: str, engine: str = "tavily") -> str:
    from src.tools.browser import search
    results = await search(query, engine=engine)
    if not results:
        return "（搜尋無結果）"
    return "\n\n".join(
        f"標題：{r['title']}\n網址：{r['url']}\n摘要：{r['snippet']}"
        for r in results
    )


async def run(user_message: str, user_id: int = 0, force_browse: str = "", force_search: bool = False) -> str:
    history = await load_history(user_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history

    if force_browse:
        page_content = await fetch_page(force_browse)
        messages.append({
            "role": "user",
            "content": f"以下是網頁內容：\n\n{page_content}\n\n{user_message}",
        })
    else:
        needs_web = force_search or _needs_search(user_message)
        if needs_web:
            engine = get_search_engine(user_id)
            logger.info(f"Search triggered [{engine}]: {user_message}")
            search_context = await _run_search(user_message, engine=engine)
            messages.append({
                "role": "user",
                "content": f"以下是網路搜尋結果，請根據這些資料回答問題：\n\n{search_context}\n\n問題：{user_message}",
            })
        else:
            messages.append({"role": "user", "content": user_message})

    if is_auto(user_id):
        reply = await chat(messages)
    else:
        model_alias = get_model(user_id)
        reply = await chat(messages, model_alias=model_alias, fallback=False)

    await save_message(user_id, "user", user_message)
    await save_message(user_id, "assistant", reply)

    return reply
