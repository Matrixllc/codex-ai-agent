from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import (
    ChunkRecord,
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    StoredArticle,
)
from app.services.chunker import chunk_text
from app.services.crawler import fetch_html
from app.services.embedder import Embedder
from app.services.extractor import extract_article
from app.services.markdown_store import MarkdownStore
from app.services.summarizer import Summarizer
from app.services.vector_store import VectorStore


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest) -> IngestResponse:
    try:
        html = await fetch_html(str(request.url))
        article = extract_article(str(request.url), html)
        chunk_texts = chunk_text(
            article.content,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        if not chunk_texts:
            raise ValueError("No chunks generated from article content")

        chunks = [
            ChunkRecord(
                chunk_id=f"{article.article_id}_chunk_{index}",
                text=text,
                chunk_index=index,
            )
            for index, text in enumerate(chunk_texts)
        ]

        summarizer = Summarizer()
        summary = summarizer.summarize(article)

        embedder = Embedder()
        embeddings = embedder.embed_texts([chunk.text for chunk in chunks])

        vector_store = VectorStore()
        vector_store.upsert_article(article, chunks, embeddings)

        markdown_store = MarkdownStore()
        markdown_path = markdown_store.write_article_card(
            article=article,
            summary=summary,
            chunks=chunks,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )

        stored = StoredArticle(
            article=article,
            chunks=chunks,
            summary=summary,
            markdown_path=str(markdown_path),
        )
        return IngestResponse(
            article_id=stored.article.article_id,
            url=stored.article.url,
            title=stored.article.title,
            chunk_count=len(stored.chunks),
            markdown_path=stored.markdown_path,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    try:
        embedder = Embedder()
        query_embedding = embedder.embed_query(request.query)
        vector_store = VectorStore()
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k or settings.top_k_default,
        )
        return SearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
