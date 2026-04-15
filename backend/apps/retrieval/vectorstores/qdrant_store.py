from __future__ import annotations

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from apps.retrieval.services.embedding_service import EmbeddingService


logger = logging.getLogger(__name__)


class QdrantStore:
    def __init__(self, settings_obj, embedding_service: EmbeddingService | None = None):
        self.settings = settings_obj
        self.collection_name = getattr(self.settings, "QDRANT_COLLECTION", "smartdocsai_documents")
        self.vector_size = int(getattr(self.settings, "EMBEDDING_VECTOR_SIZE", 1024))
        self.client = QdrantClient(
            url=getattr(self.settings, "QDRANT_URL", "http://localhost:6333"),
            api_key=getattr(self.settings, "QDRANT_API_KEY", "") or None,
            timeout=30,
        )
        self.embedding_service = embedding_service or EmbeddingService()

    def upsert_document(self, document, chunks):
        if not chunks:
            return {
                "vector_collection": self.collection_name,
                "chunk_count": 0,
            }

        self._ensure_collection()
        texts = [chunk.get("content", "") for chunk in chunks]
        vectors = self.embedding_service.embed_texts(texts)
        points = []
        for chunk, vector in zip(chunks, vectors):
            metadata = dict(chunk.get("metadata", {}))
            payload = {
                "text": chunk.get("content", ""),
                "file_id": document.id,
                "document_id": document.id,
                **metadata,
            }
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload,
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)
        return {
            "vector_collection": self.collection_name,
            "chunk_count": len(points),
        }

    def search(self, query, document_ids, limit=5):
        if not query or not document_ids:
            return []

        self._ensure_collection()
        query_vector = self.embedding_service.embed_query(query)
        query_filter = self._build_document_filter(document_ids)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        hits = []
        for result in results:
            payload = dict(result.payload or {})
            text = payload.pop("text", "")
            hits.append(
                {
                    "content": text,
                    "score": float(result.score),
                    "metadata": payload,
                }
            )
        return hits

    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection_name)
            return
        except Exception:
            logger.info("Creating missing Qdrant collection: %s", self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
        )

    def _build_document_filter(self, document_ids):
        ids = [int(value) for value in document_ids if value is not None]
        if not ids:
            return None

        if hasattr(models, "MatchAny"):
            return models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchAny(any=ids),
                    )
                ]
            )

        return models.Filter(
            should=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=value),
                )
                for value in ids
            ]
        )
