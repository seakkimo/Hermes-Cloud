from config.settings import OPENROUTER_DEFAULT_MODEL

# In-memory store: {user_id: {"model": "..."}}
_sessions: dict[int, dict] = {}


def get_model(user_id: int) -> str:
    return _sessions.get(user_id, {}).get("model", OPENROUTER_DEFAULT_MODEL)


def set_model(user_id: int, model: str) -> None:
    _sessions.setdefault(user_id, {})["model"] = model
