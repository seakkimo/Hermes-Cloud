from src.mcp.registry import Tool, register
from src.tools.browser import search, fetch_page
from src.tools.news import run as news_run
from src.memory.supabase import load_history


async def _search(query: str, engine: str = "tavily") -> str:
    results = await search(query, engine=engine)
    if not results:
        return "No results found."
    return "\n\n".join(
        f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for r in results
    )


async def _browse(url: str) -> str:
    content = await fetch_page(url)
    return content or "Could not fetch page."


async def _get_memory(user_id: int) -> str:
    history = await load_history(user_id)
    if not history:
        return "No conversation history found."
    return "\n".join(f"[{m['role']}]: {m['content']}" for m in history)


async def _news_summary() -> str:
    return await news_run()


def setup():
    register(Tool(
        name="search",
        description="Search the web using Tavily or Google News RSS",
        func=_search,
        parameters={
            "query": {"type": "string", "description": "Search query"},
            "engine": {"type": "string", "description": "Search engine: tavily or news", "default": "tavily"},
        },
    ))

    register(Tool(
        name="browse",
        description="Fetch and read the content of a webpage",
        func=_browse,
        parameters={
            "url": {"type": "string", "description": "URL to fetch"},
        },
    ))

    register(Tool(
        name="get_memory",
        description="Retrieve conversation history for a user from Supabase",
        func=_get_memory,
        parameters={
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
    ))

    register(Tool(
        name="news_summary",
        description="Fetch and summarize today's AI and Robotics news",
        func=_news_summary,
        parameters={},
    ))
