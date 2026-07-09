from src.llm.openrouter import chat
from src.agent.session import get_model, is_auto, AUTO_MODEL

SYSTEM_PROMPT = (
    "You are Hermes, a personal AI assistant. "
    "Be concise, helpful, and honest."
)


async def run(user_message: str, user_id: int = 0) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    if is_auto(user_id):
        # Auto mode: full fallback chain
        return await chat(messages)
    else:
        # Manual mode: use selected model, no fallback
        model = get_model(user_id)
        return await chat(messages, model=model, fallback=False)
