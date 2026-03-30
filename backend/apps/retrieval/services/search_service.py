from django.conf import settings

from apps.retrieval.vectorstores.qdrant_store import QdrantStore


class SearchService:
    def __init__(self, adapter=None):
        self.adapter = adapter or QdrantStore(settings)

    def search(self, query, document_ids, limit=5):
        return self.adapter.search(query=query, document_ids=document_ids, limit=limit)
