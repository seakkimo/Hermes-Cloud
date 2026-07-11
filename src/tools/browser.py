import logging
import httpx
import urllib.parse
import feedparser
import re

logger = logging.getLogger(__name__)

JINA_READER_BASE = "https://r.jina.ai/"
MAX_PAGE_CHARS = 3000


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


async def search(query: str, max_results: int = 5) -> list[dict]:
    """Search using Google News RSS feed."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:max_results]:
            results.append({
                "title": _strip_html(entry.get("title", "")),
                "url": entry.get("link", ""),
                "snippet": _strip_html(entry.get("summary", ""))[:200],
            })
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


async def fetch_page(url: str) -> str:
    """Fetch and parse a webpage via Jina Reader API (handles JS rendering)."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{JINA_READER_BASE}{url}",
                headers={"Accept": "text/plain"},
            )
            return response.text[:MAX_PAGE_CHARS]
    except Exception as e:
        logger.error(f"Page fetch error: {e}")
        return ""
