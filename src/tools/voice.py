"""Voice transcription — Telegram voice/audio → Groq Whisper → text."""
import logging
import tempfile
import os
from groq import AsyncGroq

logger = logging.getLogger(__name__)

_groq_client: AsyncGroq | None = None

def _get_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    return _groq_client


async def transcribe(file_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Transcribe audio bytes using OpenAI Whisper API."""
    try:
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1] or ".ogg", delete=False) as f:
            f.write(file_bytes)
            tmp_path = f.name
        try:
            with open(tmp_path, "rb") as audio_file:
                response = await _get_client().audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    response_format="text",
                )
            return str(response).strip()
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return ""
