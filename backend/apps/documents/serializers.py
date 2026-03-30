from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "original_filename",
            "file_path",
            "mime_type",
            "size_bytes",
            "source",
            "status",
            "processing_status",
            "summary_status",
            "summary",
            "error_message",
            "created_at",
            "updated_at",
        )


class DocumentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "status", "processing_status", "summary_status", "error_message")


class DocumentUploadSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.FileField(), allow_empty=False)
