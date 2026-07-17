from src.mcp.registry import Tool, register
from src.tools.browser import search, fetch_page
from src.tools.news import run as news_run
from src.tools.paper import run as paper_run
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


async def _paper_summary() -> str:
    return await paper_run()


async def _robot_command(action: str, speed: float = 0.3) -> str:
    """Called by Agent Loop — delegates to the live WebSocket sender in main.py."""
    from src.mcp.registry import get_tool
    tool = get_tool("robot_command")
    if not tool:
        return "Robot tool not registered (Bridge not connected?)"
    return await tool.func(command={"action": action, "speed": speed})


def setup():
    register(Tool(
        name="search",
        description="Search the web for current information, news, or any topic",
        func=_search,
        parameters={
            "query": {"type": "string", "description": "Search query"},
            "engine": {"type": "string", "description": "tavily (general) or news (Google News RSS)", "enum": ["tavily", "news"]},
        },
        required=["query"],
    ))

    register(Tool(
        name="browse",
        description="Fetch and read the full content of a webpage by URL",
        func=_browse,
        parameters={
            "url": {"type": "string", "description": "Full URL to fetch"},
        },
        required=["url"],
    ))

    register(Tool(
        name="get_memory",
        description="Retrieve conversation history for a user",
        func=_get_memory,
        parameters={
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
        required=["user_id"],
    ))

    register(Tool(
        name="news_summary",
        description="Fetch and summarize today's AI and Robotics news headlines",
        func=_news_summary,
        parameters={},
        required=[],
    ))

    register(Tool(
        name="paper_summary",
        description="Fetch and summarize the latest AI, Robotics, and UAV papers from arXiv",
        func=_paper_summary,
        parameters={},
        required=[],
    ))

    register(Tool(
        name="move_robot",
        description="Send a movement command to the physical robot via ROS2 Bridge",
        func=_robot_command,
        parameters={
            "action": {"type": "string", "description": "Movement action", "enum": ["move_forward", "move_backward", "turn_left", "turn_right", "stop"]},
            "speed": {"type": "number", "description": "Speed value 0.1-1.0, default 0.3"},
        },
        required=["action"],
    ))
