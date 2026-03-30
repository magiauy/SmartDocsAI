from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        INDEXED = "indexed", "Indexed"
        FAILED = "failed", "Failed"

    class SummaryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=255)
    size_bytes = models.PositiveBigIntegerField(default=0)
    source = models.CharField(max_length=50, default="upload")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    processing_status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    summary_status = models.CharField(max_length=20, choices=SummaryStatus.choices, default=SummaryStatus.PENDING)
    summary = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DocumentIndex(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name="index")
    vector_collection = models.CharField(max_length=255)
    chunk_count = models.PositiveIntegerField(default=0)
    index_status = models.CharField(max_length=20, default="pending")
    last_indexed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
