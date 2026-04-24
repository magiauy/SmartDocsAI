from asgiref.sync import async_to_sync
from django.conf import settings

from apps.retrieval.services.chunking_service import ChunkingService
from apps.retrieval.services.indexing_service import IndexingService
from apps.retrieval.services.normalization_service import NormalizationService
from apps.retrieval.services.summarization_service import SummarizationService
from apps.retrieval.vectorstores.factory import get_retrieval_store


def run_document_pipeline(document):
    normalization_service = NormalizationService()
    chunking_service = ChunkingService()
    indexing_service = IndexingService(get_retrieval_store(settings))
    summarization_service = SummarizationService()

    normalized = async_to_sync(normalization_service.normalize_document)(document)
    chunks = chunking_service.chunk(normalized)
    index_result = indexing_service.upsert_document(document, chunks)
    summary = summarization_service.summarize(document, chunks)
    return {
        "chunk_count": index_result["chunk_count"],
        "vector_collection": index_result["vector_collection"],
        "summary": summary["summary"],
    }
