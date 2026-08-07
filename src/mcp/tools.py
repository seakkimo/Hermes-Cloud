from src.mcp.registry import Tool, register
from src.tools.browser import search, fetch_page
from src.tools.news import run as news_run
from src.tools.paper import run as paper_run
from src.tools.calendar import add_event, list_events, delete_event
from src.tools.todo import add_todo, list_todos, complete_todo, delete_todo
from src.tools.email_tool import send_email, read_emails, read_email_body
from src.tools.code_exec import execute_python
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

    # ── V1.1 Tools ────────────────────────────────────────────────────────────

    register(Tool(
        name="calendar_add",
        description="Add a calendar event. Use for scheduling, reminders, or appointments.",
        func=add_event,
        parameters={
            "title": {"type": "string", "description": "Event title"},
            "start": {"type": "string", "description": "Start time, format: YYYY-MM-DD HH:MM or YYYY-MM-DD"},
            "end": {"type": "string", "description": "End time (optional), same format as start"},
            "description": {"type": "string", "description": "Optional event description"},
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
        required=["title", "start", "user_id"],
    ))

    register(Tool(
        name="calendar_list",
        description="List upcoming calendar events within the next N days.",
        func=list_events,
        parameters={
            "days": {"type": "integer", "description": "Number of days to look ahead, default 7"},
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
        required=["user_id"],
    ))

    register(Tool(
        name="calendar_delete",
        description="Delete a calendar event by title.",
        func=delete_event,
        parameters={
            "title": {"type": "string", "description": "Event title to delete (partial match)"},
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
        required=["title", "user_id"],
    ))

    register(Tool(
        name="email_send",
        description="Send an email to a recipient.",
        func=send_email,
        parameters={
            "to": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject"},
            "body": {"type": "string", "description": "Email body content"},
        },
        required=["to", "subject", "body"],
    ))

    register(Tool(
        name="email_read",
        description="Read the latest emails from inbox, with index numbers.",
        func=read_emails,
        parameters={
            "count": {"type": "integer", "description": "Number of emails to read, default 5"},
            "folder": {"type": "string", "description": "Mailbox folder, default INBOX"},
        },
        required=[],
    ))

    register(Tool(
        name="email_read_body",
        description="Read the full body of a specific email by its index number (1=latest). Use after email_read to get full content.",
        func=read_email_body,
        parameters={
            "index": {"type": "integer", "description": "Email index from inbox list, 1=latest"},
            "count": {"type": "integer", "description": "Pool size to pick from, default 5"},
            "folder": {"type": "string", "description": "Mailbox folder, default INBOX"},
        },
        required=["index"],
    ))

    # ── V1.6 Todo Tools ───────────────────────────────────────────────────────

    register(Tool(
        name="todo_add",
        description="Add a new todo task.",
        func=add_todo,
        parameters={
            "title": {"type": "string", "description": "Task title"},
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
        required=["title", "user_id"],
    ))

    register(Tool(
        name="todo_list",
        description="List todo tasks. By default shows only pending (undone) tasks.",
        func=list_todos,
        parameters={
            "user_id": {"type": "integer", "description": "Telegram user ID"},
            "show_done": {"type": "boolean", "description": "Include completed tasks, default false"},
        },
        required=["user_id"],
    ))

    register(Tool(
        name="todo_done",
        description="Mark a todo task as completed by title (partial match).",
        func=complete_todo,
        parameters={
            "title": {"type": "string", "description": "Task title to mark done (partial match)"},
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
        required=["title", "user_id"],
    ))

    register(Tool(
        name="todo_delete",
        description="Delete a todo task by title (partial match).",
        func=delete_todo,
        parameters={
            "title": {"type": "string", "description": "Task title to delete (partial match)"},
            "user_id": {"type": "integer", "description": "Telegram user ID"},
        },
        required=["title", "user_id"],
    ))

    register(Tool(
        name="execute_python",
        description="Execute Python code and return the output. Use for calculations, data processing, or any computation.",
        func=execute_python,
        parameters={
            "code": {"type": "string", "description": "Python code to execute"},
        },
        required=["code"],
    ))
