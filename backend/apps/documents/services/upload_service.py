from pathlib import Path

from django.db import transaction

from apps.jobs.tasks.document_tasks import process_document

from ..models import Document
from .storage import StorageService


class UploadService:
    def __init__(self, storage_service=None):
        self.storage_service = storage_service or StorageService()

    def create_documents_from_files(self, files):
        documents = []
        with transaction.atomic():
            for uploaded_file in files:
                file_path = self.storage_service.save(uploaded_file)
                document = Document.objects.create(
                    title=Path(uploaded_file.name).stem,
                    original_filename=uploaded_file.name,
                    file_path=file_path,
                    mime_type=getattr(uploaded_file, "content_type", "application/octet-stream"),
                    size_bytes=uploaded_file.size,
                    source="upload",
                    status=Document.Status.UPLOADED,
                    processing_status=Document.Status.UPLOADED,
                    summary_status=Document.SummaryStatus.PENDING,
                )
                documents.append(document)
                process_document.delay(document.id)
        return documents
