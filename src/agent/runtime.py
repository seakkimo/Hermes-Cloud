from src.llm.openrouter import chat
from src.agent.session import get_model

SYSTEM_PROMPT = (
    "You are Hermes, a personal AI assistant. "
    "Be concise, helpful, and honest."
)


async def run(user_message: str, user_id: int = 0) -> str:
    model = get_model(user_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return await chat(messages, model=model)
