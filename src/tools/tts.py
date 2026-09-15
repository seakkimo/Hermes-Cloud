"""TTS tool — edge-tts, no API key required."""
import asyncio
import tempfile
import os
import re
import edge_tts

VOICE_FEMALE_EN = "en-US-JennyNeural"
VOICE_MALE_EN   = "en-US-GuyNeural"
VOICE_ZH        = "zh-TW-HsiaoChenNeural"

RATE_NORMAL = "+0%"
RATE_SLOW   = "-25%"


def extract_english(text: str) -> str:
    """Keep only lines that are predominantly English (for TTS)."""
    lines = text.splitlines()
    en_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Count ASCII letters vs total chars
        ascii_count = sum(1 for c in stripped if c.isascii() and c.isalpha())
        total_alpha = sum(1 for c in stripped if c.isalpha())
        if total_alpha == 0:
            continue
        if ascii_count / total_alpha >= 0.6:
            en_lines.append(stripped)
    return "\n".join(en_lines) if en_lines else text


def extract_chinese(text: str) -> str:
    """Keep only lines that are predominantly Chinese."""
    lines = text.splitlines()
    zh_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        zh_count = sum(1 for c in stripped if '\u4e00' <= c <= '\u9fff')
        total_alpha = sum(1 for c in stripped if c.isalpha() or '\u4e00' <= c <= '\u9fff')
        if total_alpha == 0:
            continue
        if zh_count / total_alpha >= 0.4:
            zh_lines.append(stripped)
    return "\n".join(zh_lines) if zh_lines else ""


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
