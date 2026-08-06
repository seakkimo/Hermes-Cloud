"""Voice transcription — Telegram voice/audio → OpenAI Whisper → text."""
import logging
import tempfile
import os
from openai import AsyncOpenAI
from config.settings import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

# Whisper uses OpenAI directly (not OpenRouter — OpenRouter doesn't support audio)
_whisper_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY") or OPENROUTER_API_KEY,
    base_url="https://api.openai.com/v1",
    max_retries=0,
)


async def transcribe(file_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Transcribe audio bytes using OpenAI Whisper API."""
    try:
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1] or ".ogg", delete=False) as f:
            f.write(file_bytes)
            tmp_path = f.name
        try:
            with open(tmp_path, "rb") as audio_file:
                response = await _whisper_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                )
            return str(response).strip()
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return ""
