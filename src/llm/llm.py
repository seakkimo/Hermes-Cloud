import logging
from openai import AsyncOpenAI, RateLimitError, NotFoundError
from config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)

# Cache: loaded once per process, refreshed on demand
_models_cache: list[dict] = []


async def _load_models() -> list[dict]:
    global _models_cache
    if _models_cache:
        return _models_cache
    try:
        from src.memory.supabase import get_supabase_client
        client = get_supabase_client()
        result = (
            client.table("models")
            .select("*")
            .eq("is_active", True)
            .order("priority")
            .execute()
        )
        _models_cache = result.data or []
        logger.info(f"Loaded {len(_models_cache)} models from Supabase")
    except Exception as e:
        logger.error(f"Failed to load models from Supabase: {e}")
        _models_cache = []
    return _models_cache


def invalidate_cache():
    global _models_cache
    _models_cache = []


def _make_client(model_row: dict) -> AsyncOpenAI:
    api_key = model_row.get("api_key") or OPENROUTER_API_KEY
    base_url = model_row.get("base_url") or OPENROUTER_BASE_URL
    return AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=0)


async def get_model_by_alias(alias: str) -> dict | None:
    models = await _load_models()
    for m in models:
        if m["alias"] == alias:
            return m
    return None


async def list_models(all_models: bool = False) -> list[dict]:
    if all_models:
        try:
            from src.memory.supabase import get_supabase_client
            client = get_supabase_client()
            result = (
                client.table("models")
                .select("*")
                .order("priority")
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to load all models: {e}")
            return []
    return await _load_models()


async def chat(messages: list[dict], model_alias: str = "", fallback: bool = True) -> str:
    models = await _load_models()

    if not models:
        client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL, max_retries=0)
        from config.settings import OPENROUTER_DEFAULT_MODEL
        response = await client.chat.completions.create(
            model=OPENROUTER_DEFAULT_MODEL, messages=messages
        )
        return response.choices[0].message.content

    if model_alias:
        # Find specific model
        target = next((m for m in models if m["alias"] == model_alias), None)
        if not target:
            raise ValueError(f"Model alias '{model_alias}' not found")
        candidates = [target] if not fallback else [target] + [m for m in models if m["alias"] != model_alias]
    else:
        candidates = models  # full fallback chain by priority

    for model_row in candidates:
        try:
            client = _make_client(model_row)
            logger.info(f"Calling [{model_row['provider']}] {model_row['model_id']}")
            response = await client.chat.completions.create(
                model=model_row["model_id"],
                messages=messages,
            )
            return response.choices[0].message.content
        except (RateLimitError, NotFoundError) as e:
            if not fallback:
                raise
            logger.warning(f"Model {model_row['model_id']} unavailable ({e.status_code}), trying next...")
        except Exception as e:
            if not fallback:
                raise
            logger.warning(f"Model {model_row['model_id']} error ({e}), trying next...")

    raise RuntimeError("All models in fallback chain are unavailable.")


async def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    model_alias: str = "",
    fallback: bool = True,
) -> dict:
    """Like chat() but supports function calling. Returns {content, tool_calls}."""
    models = await _load_models()

    if not models:
        client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL, max_retries=0)
        from config.settings import OPENROUTER_DEFAULT_MODEL
        response = await client.chat.completions.create(
            model=OPENROUTER_DEFAULT_MODEL, messages=messages, tools=tools, tool_choice="auto"
        )
        msg = response.choices[0].message
        return {"content": msg.content, "tool_calls": _parse_tool_calls(msg)}

    if model_alias:
        target = next((m for m in models if m["alias"] == model_alias), None)
        if not target:
            raise ValueError(f"Model alias '{model_alias}' not found")
        candidates = [target] if not fallback else [target] + [m for m in models if m["alias"] != model_alias]
    else:
        candidates = models

    for model_row in candidates:
        try:
            client = _make_client(model_row)
            logger.info(f"[tools] Calling [{model_row['provider']}] {model_row['model_id']}")
            response = await client.chat.completions.create(
                model=model_row["model_id"],
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            msg = response.choices[0].message
            return {"content": msg.content, "tool_calls": _parse_tool_calls(msg)}
        except (RateLimitError, NotFoundError) as e:
            if not fallback:
                raise
            logger.warning(f"Model {model_row['model_id']} unavailable ({e.status_code}), trying next...")
        except Exception as e:
            if not fallback:
                raise
            logger.warning(f"Model {model_row['model_id']} error ({e}), trying next...")

    raise RuntimeError("All models in fallback chain are unavailable.")


def _parse_tool_calls(msg) -> list[dict] | None:
    if not msg.tool_calls:
        return None
    return [
        {
            "id": tc.id,
            "function": {
                "name": tc.function.name,
                "arguments": tc.function.arguments,
            },
        }
        for tc in msg.tool_calls
    ]
