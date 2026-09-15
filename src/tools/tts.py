"""TTS tool — edge-tts, no API key required."""
import re
import tempfile
import os
import edge_tts

VOICE_FEMALE_EN = "en-US-JennyNeural"
VOICE_MALE_EN   = "en-US-GuyNeural"
VOICE_ZH        = "zh-TW-HsiaoChenNeural"

RATE_NORMAL = "+0%"
RATE_SLOW   = "-25%"


def extract_article(text: str) -> str:
    """Extract only the main English sentence/article (inside quotes or first English block)."""
    # Try to find quoted English sentence first: "..." or 「...」
    match = re.search(r'["\u201c]([A-Z][^"\u201d]{20,})["\u201d]', text)
    if match:
        return match.group(1).strip()
    # Fallback: first line that is mostly English and long enough
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) < 20:
            continue
        ascii_count = sum(1 for c in stripped if c.isascii() and c.isalpha())
        total_alpha = sum(1 for c in stripped if c.isalpha())
        if total_alpha > 0 and ascii_count / total_alpha >= 0.8:
            return stripped
    return ""


def extract_vocab(text: str) -> list[str]:
    """Extract vocabulary words from markdown table (first column)."""
    words = []
    for line in text.splitlines():
        # Match markdown table rows: | word | ...
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cols:
            continue
        word = cols[0].strip()
        # Skip header/separator rows
        if not word or word.startswith("-") or word.lower() in ("單字 / 片語", "word", "vocab"):
            continue
        # Keep only the base word (before space or /)
        base = re.split(r'[/\s]', word)[0].strip()
        if base and base.isascii() and base.replace("-", "").isalpha():
            words.append(base)
    return words[:8]  # max 8 buttons


async def synthesize(text: str, voice: str = VOICE_FEMALE_EN, rate: str = RATE_NORMAL) -> bytes:
    """Convert text to MP3 bytes using edge-tts."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    try:
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)
