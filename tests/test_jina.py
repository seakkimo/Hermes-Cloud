import asyncio
import httpx
import urllib.parse

async def test():
    query = urllib.parse.quote("bavi typhoon 2026")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"https://s.jina.ai/{query}",
            headers={"Accept": "application/json"},
        )
        print("Status:", r.status_code)
        print("Response:", r.text[:1000])

asyncio.run(test())
