from __future__ import annotations

import json

from openai import OpenAI

from app.config import settings
from app.models.schemas import ArticleSummary, ExtractedArticle


PROMPT = """You are helping build a human-readable article knowledge card.
Return compact JSON with keys: overview, summary, keywords.

Rules:
- overview: 2-4 Chinese sentences describing what the article is about and who it is useful for
- summary: 3-6 Chinese sentences summarizing the article content
- keywords: 3-8 short keywords, preferably lowercase English technical terms when applicable
- Do not wrap the JSON in markdown
"""


class Summarizer:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def summarize(self, article: ExtractedArticle) -> ArticleSummary:
        preview = article.content[:6000]
        response = self.client.responses.create(
            model=settings.openai_chat_model,
            input=[
                {"role": "system", "content": PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"title: {article.title}\n"
                        f"url: {article.url}\n"
                        f"content:\n{preview}"
                    ),
                },
            ],
        )
        text = response.output_text
        data = json.loads(text)
        return ArticleSummary.model_validate(data)
