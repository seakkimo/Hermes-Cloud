import feedparser
from src.llm.llm import chat

FEEDS = {
    "AI": "https://news.google.com/rss/search?q=artificial+intelligence&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "Robotics": "https://news.google.com/rss/search?q=robotics&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
}

MAX_ITEMS_PER_FEED = 5


def _fetch_headlines(feed_url: str, max_items: int = MAX_ITEMS_PER_FEED) -> list[str]:
    feed = feedparser.parse(feed_url)
    return [entry.title for entry in feed.entries[:max_items]]


async def run() -> str:
    all_headlines = []
    for topic, url in FEEDS.items():
        headlines = _fetch_headlines(url)
        all_headlines.append(f"【{topic}】\n" + "\n".join(f"- {h}" for h in headlines))

    headlines_text = "\n\n".join(all_headlines)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一個新聞摘要助理。"
                "請將以下新聞標題整理成簡潔的中文摘要，每個主題 3-5 句話，重點突出最重要的趨勢。"
            ),
        },
        {
            "role": "user",
            "content": f"請摘要以下今日新聞：\n\n{headlines_text}",
        },
    ]

    summary = await chat(messages)
    return f"📰 *今日科技新聞摘要*\n\n{summary}"
