import arxiv
from src.llm.openrouter import chat

TOPICS = {
    "AI": "artificial intelligence machine learning",
    "Robotics": "robotics",
    "無人機": "UAV drone autonomous aerial vehicle",
}

MAX_PAPERS_PER_TOPIC = 3


def _fetch_papers(query: str, max_results: int = MAX_PAPERS_PER_TOPIC) -> list[dict]:
    client = arxiv.Client(num_retries=1, delay_seconds=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    papers = []
    try:
        for result in client.results(search):
            papers.append({
                "title": result.title,
                "summary": result.summary[:300],
                "url": result.entry_id,
            })
    except Exception:
        pass
    return papers


async def run() -> str:
    all_sections = []

    for topic, query in TOPICS.items():
        papers = _fetch_papers(query)
        if not papers:
            continue

        papers_text = "\n\n".join(
            f"標題：{p['title']}\n摘要：{p['summary']}\n連結：{p['url']}"
            for p in papers
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一個學術論文摘要助理。"
                    "請將以下論文整理成簡潔的繁體中文摘要，每篇一句話說明核心貢獻，並保留論文連結。"
                ),
            },
            {
                "role": "user",
                "content": f"請摘要以下【{topic}】最新論文：\n\n{papers_text}",
            },
        ]

        summary = await chat(messages)
        all_sections.append(f"*【{topic}】*\n{summary}")

    body = "\n\n".join(all_sections)
    return f"📄 *今日論文摘要*\n\n{body}"
