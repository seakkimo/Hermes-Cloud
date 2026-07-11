import logging
import httpx

logger = logging.getLogger(__name__)

JINA_READER_BASE = "https://r.jina.ai/"
JINA_SEARCH_BASE = "https://s.jina.ai/"
MAX_PAGE_CHARS = 3000
MAX_SEARCH_CHARS = 4000


def search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web using Jina Search API."""
    import urllib.parse
    try:
        encoded = urllib.parse.quote(query)
        import asyncio
        return asyncio.get_event_loop().run_until_complete(_async_search(encoded))
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


async def _async_search(encoded_query: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{JINA_SEARCH_BASE}{encoded_query}",
            headers={"Accept": "application/json", "X-Respond-With": "no-content"},
        )
        data = response.json()
        results = data.get("data", [])
        return [
            {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")}
            for r in results
        ]


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
