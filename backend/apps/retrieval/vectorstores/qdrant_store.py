class QdrantStore:
    def __init__(self, settings_obj):
        self.settings = settings_obj

    def upsert_document(self, document, chunks):
        return {
            "vector_collection": getattr(self.settings, "QDRANT_COLLECTION", "smartdocsai_documents"),
            "chunk_count": len(chunks),
        }

    def search(self, query, document_ids, limit=5):
        return [
            {
                "content": f"Context for {query}",
                "score": 1.0,
                "metadata": {"document_id": document_ids[0] if document_ids else None},
            }
        ][:limit]
