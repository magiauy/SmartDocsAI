from __future__ import annotations

import json
import logging
import re
import time
from typing import LiteralString, cast

from apps.retrieval.services.embedding_service import EmbeddingService

try:
    from neo4j import GraphDatabase, basic_auth
except ImportError:
    GraphDatabase = None
    basic_auth = None


logger = logging.getLogger(__name__)


class Neo4jStore:
    def __init__(self, settings_obj, embedding_service: EmbeddingService | None = None):
        if GraphDatabase is None:
            raise RuntimeError("neo4j package is required for RETRIEVAL_STORE_BACKEND=neo4j")
        if basic_auth is None:
            raise RuntimeError("neo4j package is required for RETRIEVAL_STORE_BACKEND=neo4j")

        self.settings = settings_obj
        self.embedding_service = embedding_service or EmbeddingService()
        self.uri = getattr(self.settings, "NEO4J_URI", "bolt://localhost:7687")
        self.user = getattr(self.settings, "NEO4J_USER", "neo4j")
        self.password = getattr(self.settings, "NEO4J_PASSWORD", "")
        self.database = getattr(self.settings, "NEO4J_DATABASE", "neo4j")
        self.vector_size = int(getattr(self.settings, "EMBEDDING_VECTOR_SIZE", 1024))
        self.vector_index_name = self._safe_identifier(
            getattr(self.settings, "NEO4J_VECTOR_INDEX_NAME", "smartdocsai_chunk_embedding_index")
        )
        self.similarity = self._safe_similarity(
            getattr(self.settings, "NEO4J_VECTOR_SIMILARITY", "cosine")
        )
        # Always send a basic auth token to avoid server-side "missing key scheme" errors.
        self.driver = GraphDatabase.driver(self.uri, auth=basic_auth(self.user, self.password))

    def upsert_document(self, document, chunks):
        if not chunks:
            return {
                "vector_collection": self.vector_index_name,
                "chunk_count": 0,
            }

        self._ensure_schema()
        texts = [chunk.get("content", "") for chunk in chunks]
        vectors = self.embedding_service.embed_texts(texts)
        rows = []
        for chunk, vector in zip(chunks, vectors):
            metadata = dict(chunk.get("metadata", {}))
            chunk_index = int(metadata.get("chunk_index", 0))
            rows.append(
                {
                    "chunk_uid": f"{document.id}:{chunk_index}",
                    "chunk_index": chunk_index,
                    "content": chunk.get("content", ""),
                    "embedding": vector,
                    "metadata_json": json.dumps(metadata, ensure_ascii=False, default=str),
                }
            )

        statement = """
        MERGE (d:Document {document_id: $document_id})
        SET d.title = $title, d.updated_at = datetime()
        WITH d
        OPTIONAL MATCH (d)-[:HAS_CHUNK]->(old:Chunk)
        DETACH DELETE old
        WITH d
        UNWIND $rows AS row
        CREATE (c:Chunk {
            chunk_uid: row.chunk_uid,
            document_id: $document_id,
            chunk_index: row.chunk_index,
            content: row.content,
            embedding: row.embedding,
            metadata_json: row.metadata_json
        })
        MERGE (d)-[:HAS_CHUNK]->(c)
        WITH row, c
        ORDER BY row.chunk_index ASC
        WITH collect(c) AS created_chunks
        UNWIND range(0, size(created_chunks) - 2) AS i
        WITH created_chunks[i] AS left_chunk, created_chunks[i + 1] AS right_chunk
        MERGE (left_chunk)-[:NEXT]->(right_chunk)
        """

        with self.driver.session(database=self.database) as session:
            session.run(
                cast(LiteralString, statement),
                document_id=int(document.id),
                title=document.title,
                rows=rows,
            ).consume()

        return {
            "vector_collection": self.vector_index_name,
            "chunk_count": len(rows),
        }

    def search(self, query, document_ids, limit=5):
        hits, _ = self.search_with_metrics(query=query, document_ids=document_ids, limit=limit)
        return hits

    def search_with_metrics(self, query, document_ids, limit=5):
        if not query or not document_ids:
            return [], {"embedding_ms": 0, "query_ms": 0, "total_ms": 0}

        self._ensure_schema()
        started_at = time.perf_counter()

        embedding_started_at = time.perf_counter()
        query_vector = self.embedding_service.embed_query(query)
        embedding_ms = int((time.perf_counter() - embedding_started_at) * 1000)

        query_started_at = time.perf_counter()
        candidate_limit = max(int(limit) * 5, int(limit))
        query_statement = """
        CALL db.index.vector.queryNodes($index_name, $candidate_limit, $query_vector)
        YIELD node, score
        WHERE node.document_id IN $document_ids
        RETURN node.content AS content,
               score AS score,
               node.document_id AS document_id,
               node.chunk_index AS chunk_index,
             node.metadata_json AS metadata_json
        ORDER BY score DESC
        LIMIT $limit
        """

        hits = []
        with self.driver.session(database=self.database) as session:
            records = session.run(
                cast(LiteralString, query_statement),
                index_name=self.vector_index_name,
                candidate_limit=candidate_limit,
                query_vector=query_vector,
                document_ids=[int(value) for value in document_ids],
                limit=int(limit),
            )
            for record in records:
                raw_metadata = record.get("metadata_json")
                try:
                    metadata = json.loads(raw_metadata) if raw_metadata else {}
                except (TypeError, json.JSONDecodeError):
                    metadata = {}
                metadata.setdefault("document_id", record.get("document_id"))
                metadata.setdefault("chunk_index", record.get("chunk_index"))
                hits.append(
                    {
                        "content": record.get("content", ""),
                        "score": float(record.get("score", 0.0)),
                        "metadata": metadata,
                    }
                )

        query_ms = int((time.perf_counter() - query_started_at) * 1000)
        return hits, {
            "embedding_ms": embedding_ms,
            "query_ms": query_ms,
            "total_ms": int((time.perf_counter() - started_at) * 1000),
        }

    def _ensure_schema(self):
        index_statement = (
            f"CREATE VECTOR INDEX {self.vector_index_name} IF NOT EXISTS "
            "FOR (c:Chunk) ON (c.embedding) "
            "OPTIONS {indexConfig: {"
            f"`vector.dimensions`: {self.vector_size}, `vector.similarity_function`: '{self.similarity}'"
            "}}"
        )

        with self.driver.session(database=self.database) as session:
            session.run(
                "CREATE CONSTRAINT smartdocsai_document_id IF NOT EXISTS "
                "FOR (d:Document) REQUIRE d.document_id IS UNIQUE"
            ).consume()
            session.run(
                "CREATE CONSTRAINT smartdocsai_chunk_uid IF NOT EXISTS "
                "FOR (c:Chunk) REQUIRE c.chunk_uid IS UNIQUE"
            ).consume()
            session.run(cast(LiteralString, index_statement)).consume()

    def _safe_identifier(self, value: str) -> str:
        identifier = (value or "").strip()
        if not identifier or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
            raise ValueError("NEO4J_VECTOR_INDEX_NAME must match [A-Za-z_][A-Za-z0-9_]*")
        return identifier

    def _safe_similarity(self, value: str) -> str:
        similarity = (value or "").strip().lower()
        if similarity not in {"cosine", "euclidean"}:
            raise ValueError("NEO4J_VECTOR_SIMILARITY must be one of: cosine, euclidean")
        return similarity