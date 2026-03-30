from celery import shared_task

from apps.documents.models import Document, DocumentIndex
from apps.retrieval.langchain.pipelines import run_document_pipeline


@shared_task
def process_document(document_id: int):
    document = Document.objects.get(pk=document_id)
    document.processing_status = Document.Status.PROCESSING
    document.status = Document.Status.PROCESSING
    document.save(update_fields=["processing_status", "status", "updated_at"])
    try:
        result = run_document_pipeline(document)
        DocumentIndex.objects.update_or_create(
            document=document,
            defaults={
                "vector_collection": result["vector_collection"],
                "chunk_count": result["chunk_count"],
                "index_status": "ready",
            },
        )
        document.processing_status = Document.Status.INDEXED
        document.status = Document.Status.INDEXED
        document.summary_status = Document.SummaryStatus.READY
        document.summary = result["summary"]
        document.error_message = ""
    except Exception as exc:
        document.processing_status = Document.Status.FAILED
        document.status = Document.Status.FAILED
        document.summary_status = Document.SummaryStatus.FAILED
        document.error_message = str(exc)
    document.save()
