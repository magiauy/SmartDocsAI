from apps.documents.models import DocumentIndex


class IndexingService:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def upsert_document(self, document, chunks):
        result = self.vector_store.upsert_document(document, chunks)
        DocumentIndex.objects.update_or_create(
            document=document,
            defaults={
                "vector_collection": result["vector_collection"],
                "chunk_count": result["chunk_count"],
                "index_status": "ready",
            },
        )
        return result
