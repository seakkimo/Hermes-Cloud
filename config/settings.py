import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]

# OpenRouter
OPENROUTER_API_KEY: str = os.environ["OPENROUTER_API_KEY"]
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL: str = os.getenv(
    "OPENROUTER_DEFAULT_MODEL", "google/gemma-4-31b-it:free"
)
# Fallback chain: tried in order when primary model returns 429/404
OPENROUTER_FALLBACK_MODELS: list[str] = [
    "google/gemma-4-31b-it:free",
    "google/gemma-3-27b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "poolside/laguna-m.1:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "cohere/north-mini-code:free",
    "poolside/laguna-xs-2.1:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-20b:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-content-safety:free",
    "qwen/qwen3-coder:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "meta-llama/llama-4-scout:free",
    "mistralai/mistral-7b-instruct:free",
    # Paid fallback: only used when all free models are unavailable
    "deepseek/deepseek-r1",
]

# App
APP_ENV: str = os.getenv("APP_ENV", "development")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Render
RENDER_EXTERNAL_URL: str = os.getenv("RENDER_EXTERNAL_URL", "")
PORT: int = int(os.getenv("PORT", "8000"))
