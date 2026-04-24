import logging
import time

from django.conf import settings

from apps.retrieval.vectorstores.factory import get_retrieval_store


logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, adapter=None):
        self.adapter = adapter or get_retrieval_store(settings)

    def search(self, query, document_ids, limit=None):
        hits, _ = self.search_with_metrics(query=query, document_ids=document_ids, limit=limit)
        return hits

    def search_with_metrics(self, query, document_ids, limit=None):
        resolved_limit = int(limit or getattr(settings, "RETRIEVAL_TOP_K", 5))
        started_at = time.perf_counter()
        try:
            hits, metrics = self.adapter.search_with_metrics(query=query, document_ids=document_ids, limit=resolved_limit)
            metrics = metrics or {}
            metrics.setdefault("embedding_ms", 0)
            metrics.setdefault("query_ms", 0)
            metrics.setdefault("total_ms", int((time.perf_counter() - started_at) * 1000))
            return hits, metrics
        except Exception:
            logger.exception("Retrieval search failed")
            return [], {"embedding_ms": 0, "query_ms": 0, "total_ms": int((time.perf_counter() - started_at) * 1000)}
