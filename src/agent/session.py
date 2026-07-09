from config.settings import OPENROUTER_DEFAULT_MODEL

# Sentinel value to indicate auto/fallback mode
AUTO_MODEL = "__auto__"

# In-memory store: {user_id: {"model": "..."}}
_sessions: dict[int, dict] = {}


def get_model(user_id: int) -> str:
    return _sessions.get(user_id, {}).get("model", AUTO_MODEL)


def set_model(user_id: int, model: str) -> None:
    _sessions.setdefault(user_id, {})["model"] = model


def is_auto(user_id: int) -> bool:
    return get_model(user_id) == AUTO_MODEL
