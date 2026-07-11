import logging
import httpx
import urllib.parse
import feedparser
import re
from config.settings import TAVILY_API_KEY

logger = logging.getLogger(__name__)

JINA_READER_BASE = "https://r.jina.ai/"
MAX_PAGE_CHARS = 3000

SEARCH_ENGINES = ["tavily", "news"]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


async def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """Search using Tavily API."""
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set, falling back to news")
        return await search_news(query, max_results)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
            )
            data = response.json()
            results = data.get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:200],
                }
                for r in results
            ]
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return []


async def search_news(query: str, max_results: int = 5) -> list[dict]:
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
        logger.error(f"News search error: {e}")
        return []


async def search(query: str, engine: str = "tavily", max_results: int = 5) -> list[dict]:
    """Unified search interface."""
    if engine == "news":
        return await search_news(query, max_results)
    return await search_tavily(query, max_results)


async def fetch_page(url: str) -> str:
    """Fetch and parse a webpage via Jina Reader API."""
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
