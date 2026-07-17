import json
import logging
from src.llm.llm import chat, chat_with_tools, chat_with_tools
from src.agent.session import get_model, is_auto, get_search_engine
from src.memory.supabase import load_history, save_message
from src.tools.browser import fetch_page

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Hermes, a personal AI assistant. "
    "Be concise, helpful, and honest. "
    "Use tools when you need current information, need to browse the web, or control the robot. "
    "Respond in the same language as the user."
)

MAX_TOOL_ROUNDS = 5  # prevent infinite loops


async def run(
    user_message: str,
    user_id: int = 0,
    force_browse: str = "",
    force_search: bool = False,
) -> str:
    history = await load_history(user_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
        return reply

    if force_search:
        engine = get_search_engine(user_id)
        search_context = await _run_search(user_message, engine)
        messages.append({
            "role": "user",
            "content": f"以下是網路搜尋結果，請根據這些資料回答問題：\n\n{search_context}\n\n問題：{user_message}",
        })
        reply = await _llm(messages, user_id)
        await _save(user_id, user_message, reply)
        return reply

    # ── Agent Loop (Function Calling) ─────────────────────────────────────────
    messages.append({"role": "user", "content": user_message})

    from src.mcp.registry import to_openai_schema, call_tool
    tools = to_openai_schema()

    for round_num in range(MAX_TOOL_ROUNDS):
        model_alias = "" if is_auto(user_id) else get_model(user_id)
        fallback = is_auto(user_id)

        response = await chat_with_tools(
            messages=messages,
            tools=tools,
            model_alias=model_alias,
            fallback=fallback,
        )

        # No tool call → final answer
        if not response.get("tool_calls"):
            reply = response["content"] or ""
            break

        # Execute all tool calls in this round
        messages.append({
            "role": "assistant",
            "content": response.get("content"),
            "tool_calls": response["tool_calls"],
        })

        for tc in response["tool_calls"]:
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
        # Exceeded max rounds — ask LLM to summarise what it has
        reply = await _llm(messages, user_id)

    await _save(user_id, user_message, reply)
    return reply


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
