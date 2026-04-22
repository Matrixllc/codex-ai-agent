from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class IngestRequest(BaseModel):
    url: HttpUrl


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class IngestResponse(BaseModel):
    article_id: str
    url: str
    title: str
    chunk_count: int
    markdown_path: str
    status: str = "success"


class SearchResult(BaseModel):
    score: float
    text: str
    title: str
    url: str
    chunk_index: int
    article_id: str


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ArticleSummary(BaseModel):
    overview: str
    summary: str
    keywords: list[str]


class ExtractedArticle(BaseModel):
    article_id: str
    url: str
    source: str
    title: str
    content: str
    published_at: str | None = None
    ingested_at: datetime


class ChunkRecord(BaseModel):
    chunk_id: str
    text: str
    chunk_index: int


class StoredArticle(BaseModel):
    article: ExtractedArticle
    chunks: list[ChunkRecord]
    summary: ArticleSummary
    markdown_path: str
