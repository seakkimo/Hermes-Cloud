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
    in_table = False
    header_skipped = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break  # table ended
            continue
        in_table = True
        cols = [c.strip() for c in stripped.strip("|").split("|")]
        if not cols:
            continue
        word = cols[0].strip()
        # Skip separator rows (---|---)
        if set(word.replace("-", "").replace(" ", "")) <= set("-"):
            continue
        # Skip header row (contains Chinese or known header keywords)
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in word)
        if has_chinese or word.lower() in ("word", "vocab", "term"):
            header_skipped = True
            continue
        if not header_skipped:
            header_skipped = True  # treat first row as header
            continue
        # Accept English words and short phrases (allow spaces and hyphens)
        clean = re.sub(r'[^a-zA-Z\s\-]', '', word).strip()
        if clean and 1 <= len(clean.split()) <= 3:
            words.append(clean)
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
