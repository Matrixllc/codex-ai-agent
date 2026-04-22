from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.models.schemas import ChunkRecord, ExtractedArticle, ArticleSummary


class MarkdownStore:
    def __init__(self, root_path: Path | None = None) -> None:
        self.root_path = root_path or settings.knowledge_base_path
        self.root_path.mkdir(parents=True, exist_ok=True)

    def write_article_card(
        self,
        article: ExtractedArticle,
        summary: ArticleSummary,
        chunks: list[ChunkRecord],
        chunk_size: int,
        overlap: int,
    ) -> Path:
        path = self.root_path / f"{article.article_id}.md"
        preview = "\n\n".join(chunk.text for chunk in chunks[:2]).strip()
        keywords = "\n".join(f"- {keyword}" for keyword in summary.keywords)
        content = f"""# {article.title}

## Basic Info

- article_id: {article.article_id}
- url: {article.url}
- source: {article.source}
- published_at: {article.published_at or "unknown"}
- ingested_at: {article.ingested_at.isoformat()}

## Overview

{summary.overview}

## Summary

{summary.summary}

## Keywords

{keywords or "- none"}

## Content Preview

{preview or "No preview available."}

## Chunk Info

- chunk_count: {len(chunks)}
- chunk_size: {chunk_size}
- overlap: {overlap}

## Review Notes

- status: pending_review
"""
        path.write_text(content, encoding="utf-8")
        return path
