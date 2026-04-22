from __future__ import annotations

import re
import json
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlparse

import trafilatura

from app.models.schemas import ExtractedArticle


def _clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_article(url: str, html: str) -> ExtractedArticle:
    extracted = trafilatura.extract(
        html,
        with_metadata=True,
        include_links=False,
        include_images=False,
        favor_precision=True,
        output_format="json",
    )
    if not extracted:
        raise ValueError("Failed to extract article content")

    data = json.loads(extracted)
    raw_text = data.get("text", "")
    content = _clean_text(raw_text)
    if not content:
        raise ValueError("Extracted article content is empty")

    title = (data.get("title") or url).strip()
    article_id = sha256(url.encode("utf-8")).hexdigest()[:12]
    published_at = data.get("date")
    source = urlparse(url).netloc

    return ExtractedArticle(
        article_id=article_id,
        url=url,
        source=source,
        title=title,
        content=content,
        published_at=published_at,
        ingested_at=datetime.now(timezone.utc),
    )
