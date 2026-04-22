from __future__ import annotations

from typing import Any

import chromadb

from app.config import settings
from app.models.schemas import ChunkRecord, ExtractedArticle, SearchResult


class VectorStore:
    def __init__(self, collection_name: str = "articles") -> None:
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert_article(
        self,
        article: ExtractedArticle,
        chunks: list[ChunkRecord],
        embeddings: list[list[float]],
    ) -> None:
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            metadatas.append(
                {
                    "article_id": article.article_id,
                    "chunk_index": chunk.chunk_index,
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at or "",
                    "ingested_at": article.ingested_at.isoformat(),
                    "content_length": len(chunk.text),
                }
            )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        items: list[SearchResult] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            score = 1.0 / (1.0 + float(distance))
            items.append(
                SearchResult(
                    score=score,
                    text=document,
                    title=str(metadata.get("title", "")),
                    url=str(metadata.get("url", "")),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    article_id=str(metadata.get("article_id", "")),
                )
            )
        return items
