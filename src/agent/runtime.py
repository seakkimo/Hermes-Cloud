import json
import logging
from datetime import datetime, timezone, timedelta
from src.llm.llm import chat, chat_with_tools
from src.agent.session import get_model, is_auto, get_search_engine
from src.memory.supabase import load_history, save_message
from src.tools.browser import fetch_page

logger = logging.getLogger(__name__)

TZ_TAIPEI = timezone(timedelta(hours=8))
MAX_TOOL_ROUNDS = 3
MAX_REPLY_CHARS = 3800  # Telegram limit is 4096, leave buffer

# Models that do NOT support function calling — skip tool loop for these
NO_TOOL_CALL_MODELS = {
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "nvidia/nemotron-3.5-content-safety:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "mistralai/mistral-7b-instruct:free",
}


def _system_prompt() -> str:
    now = datetime.now(TZ_TAIPEI).strftime("%Y-%m-%d %H:%M %Z")
    return (
        f"You are Hermes, a personal AI assistant. "
        f"Current date and time: {now}. "
        f"Be concise, helpful, and honest. "
        f"Use tools when you need current information, need to browse the web, or control the robot. "
        f"Respond in the same language as the user."
    )


def _truncate(text: str) -> str:
    if len(text) <= MAX_REPLY_CHARS:
        return text
    return text[:MAX_REPLY_CHARS] + "\n\n…（訊息過長，已截斷）"


async def run(
    user_message: str,
    user_id: int = 0,
    force_browse: str = "",
    force_search: bool = False,
) -> str:
    history = await load_history(user_id)
    messages = [{"role": "system", "content": _system_prompt()}]
    messages += history

    # ── Force modes (bypass LLM tool decision) ────────────────────────────────
    if force_browse:
        page_content = await fetch_page(force_browse)
        messages.append({
            "role": "user",
            "content": f"以下是網頁內容：\n\n{page_content}\n\n{user_message}",
        })
        reply = await _llm(messages, user_id)
        await _save(user_id, user_message, reply)
        return _truncate(reply)

    if force_search:
        engine = get_search_engine(user_id)
        search_context = await _run_search(user_message, engine)
        messages.append({
            "role": "user",
            "content": f"以下是網路搜尋結果，請根據這些資料回答問題：\n\n{search_context}\n\n問題：{user_message}",
        })
        reply = await _llm(messages, user_id)
        await _save(user_id, user_message, reply)
        return _truncate(reply)

    # ── Agent Loop (Function Calling) ─────────────────────────────────────────
    messages.append({"role": "user", "content": user_message})

    model_alias = "" if is_auto(user_id) else get_model(user_id)
    fallback = is_auto(user_id)

    # Check if active model supports tool calling
    use_tools = True
    if not fallback and model_alias:
        from src.llm.llm import get_model_by_alias
        m = await get_model_by_alias(model_alias)
        if m and m["model_id"] in NO_TOOL_CALL_MODELS:
            use_tools = False

    if not use_tools:
        reply = await _llm(messages, user_id)
        await _save(user_id, user_message, reply)
        return _truncate(reply)

    from src.mcp.registry import to_openai_schema, call_tool
    tools = to_openai_schema()

    reply = ""
    for round_num in range(MAX_TOOL_ROUNDS):
        try:
            response = await chat_with_tools(
                messages=messages,
                tools=tools,
                model_alias=model_alias,
                fallback=fallback,
            )
        except Exception as e:
            logger.error(f"chat_with_tools error: {e}")
            reply = await _llm(messages, user_id)
            break

        tool_calls = response.get("tool_calls")
        content = response.get("content") or ""

        # No tool call → final answer
        if not tool_calls:
            reply = content
            break

        # Execute all tool calls in this round
        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": tool_calls,
        })

        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            try:
                arguments = json.loads(tc["function"]["arguments"])
            except Exception:
                arguments = {}

            logger.info(f"[Agent Loop round {round_num+1}] calling tool: {tool_name}({arguments})")
            try:
                result = await call_tool(tool_name, arguments)
            except Exception as e:
                result = f"Tool error: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": str(result),
            })
    else:
        # Exceeded max rounds — summarise
        reply = await _llm(messages, user_id)

    if not reply:
        reply = await _llm(messages, user_id)

    await _save(user_id, user_message, reply)
    return _truncate(reply)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _llm(messages: list[dict], user_id: int) -> str:
    if is_auto(user_id):
        return await chat(messages)
    return await chat(messages, model_alias=get_model(user_id), fallback=False)


async def _run_search(query: str, engine: str = "tavily") -> str:
    from src.tools.browser import search
    results = await search(query, engine=engine)
    if not results:
        return "（搜尋無結果）"
    return "\n\n".join(
        f"標題：{r['title']}\n網址：{r['url']}\n摘要：{r['snippet']}"
        for r in results
    )


async def _save(user_id: int, user_message: str, reply: str) -> None:
    await save_message(user_id, "user", user_message)
    await save_message(user_id, "assistant", reply)
