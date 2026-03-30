import pytest


@pytest.mark.django_db
def test_process_document_updates_summary_and_index_status(mocker):
    from apps.documents.models import Document
    from apps.jobs.tasks.document_tasks import process_document

    document = Document.objects.create(
        title="Doc",
        original_filename="doc.txt",
        file_path="media/doc.txt",
        mime_type="text/plain",
        size_bytes=10,
        source="upload",
        status="uploaded",
        processing_status="uploaded",
        summary_status="pending",
    )

    mocker.patch(
        "apps.jobs.tasks.document_tasks.run_document_pipeline",
        return_value={
            "chunk_count": 2,
            "vector_collection": "smartdocsai_documents",
            "summary": "Short summary",
        },
    )

    process_document(document.id)
    document.refresh_from_db()

    assert document.processing_status == "indexed"
    assert document.summary_status == "ready"
    assert document.summary == "Short summary"
