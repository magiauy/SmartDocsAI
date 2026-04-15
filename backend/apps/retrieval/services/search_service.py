import logging

from django.conf import settings

from apps.retrieval.vectorstores.qdrant_store import QdrantStore


logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, adapter=None):
        self.adapter = adapter or QdrantStore(settings)

    def search(self, query, document_ids, limit=None):
        resolved_limit = int(limit or getattr(settings, "RETRIEVAL_TOP_K", 5))
        try:
            return self.adapter.search(query=query, document_ids=document_ids, limit=resolved_limit)
        except Exception:
            logger.exception("Retrieval search failed")
            return []
