from src.llm.openrouter import chat
from src.agent.session import get_model, is_auto
from src.memory.supabase import load_history, save_message

SYSTEM_PROMPT = (
    "You are Hermes, a personal AI assistant. "
    "Be concise, helpful, and honest."
)


async def run(user_message: str, user_id: int = 0) -> str:
    history = await load_history(user_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    if is_auto(user_id):
        reply = await chat(messages)
    else:
        model = get_model(user_id)
        reply = await chat(messages, model=model, fallback=False)

    await save_message(user_id, "user", user_message)
    await save_message(user_id, "assistant", reply)

    return reply
