from apps.chat.models import Conversation, Message
from apps.documents.models import Document


def build_sample_documents():
    return [
        Document.objects.create(
            title="Sample",
            original_filename="sample.txt",
            file_path="media/sample.txt",
            mime_type="text/plain",
            size_bytes=10,
            source="seed",
            status="indexed",
            processing_status="indexed",
            summary_status="ready",
            summary="Sample summary",
        )
    ]


def build_sample_conversation():
    conversation = Conversation.objects.create(title="Sample conversation", provider="mock", model="mock-1", status="ready")
    Message.objects.create(conversation=conversation, role="assistant", content="Sample bootstrap")
    return conversation
