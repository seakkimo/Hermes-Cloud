import logging
import httpx
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

JINA_BASE = "https://r.jina.ai/"
MAX_SEARCH_RESULTS = 5
MAX_PAGE_CHARS = 3000


def search(query: str, max_results: int = MAX_SEARCH_RESULTS) -> list[dict]:
    """Search the web using DuckDuckGo, return list of {title, url, snippet}."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in results]
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


async def fetch_page(url: str) -> str:
    """Fetch and parse a webpage via Jina Reader API (handles JS rendering)."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{JINA_BASE}{url}",
                headers={"Accept": "text/plain"},
            )
            return response.text[:MAX_PAGE_CHARS]
    except Exception as e:
        logger.error(f"Page fetch error: {e}")
        return ""
