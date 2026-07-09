import logging
from openai import AsyncOpenAI, RateLimitError, NotFoundError
from config.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_DEFAULT_MODEL,
    OPENROUTER_FALLBACK_MODELS,
)

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)


async def chat(messages: list[dict], model: str = OPENROUTER_DEFAULT_MODEL) -> str:
    # Build fallback chain: preferred model first, then the rest
    candidates = [model] + [m for m in OPENROUTER_FALLBACK_MODELS if m != model]

    for candidate in candidates:
        try:
            logger.info(f"Calling model: {candidate}")
            response = await _client.chat.completions.create(
                model=candidate,
                messages=messages,
            )
            return response.choices[0].message.content
        except (RateLimitError, NotFoundError) as e:
            logger.warning(f"Model {candidate} unavailable ({e.status_code}), trying next...")

    raise RuntimeError("All models in fallback chain are unavailable.")
