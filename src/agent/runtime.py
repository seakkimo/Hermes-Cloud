from src.llm.openrouter import chat

SYSTEM_PROMPT = (
    "You are Hermes, a personal AI assistant. "
    "Be concise, helpful, and honest."
)


async def run(user_message: str) -> str:
    """
    Agent entry point.
    V0.1: simple pass-through to LLM.
    Future: tool calling, memory, multi-agent routing.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return await chat(messages)
