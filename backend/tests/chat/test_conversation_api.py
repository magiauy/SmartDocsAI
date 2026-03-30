import pytest


@pytest.mark.django_db
def test_create_conversation_starts_in_preparing_when_documents_not_ready(api_client, mocker):
    from apps.chat.models import Conversation
    from apps.documents.models import Document

    mocked_delay = mocker.patch("apps.chat.services.conversation_service.prepare_conversation.delay")
    document = Document.objects.create(
        title="Draft",
        original_filename="draft.txt",
        file_path="media/draft.txt",
        mime_type="text/plain",
        size_bytes=10,
        source="upload",
        status="uploaded",
        processing_status="uploaded",
        summary_status="pending",
    )

    response = api_client.post(
        "/api/conversations/",
        {"title": "Chat 1", "provider": "mock", "model": "mock-1", "document_ids": [document.id]},
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["status"] == "preparing"
    assert Conversation.objects.count() == 1
    assert mocked_delay.call_count == 1


@pytest.mark.django_db
def test_conversation_can_attach_multiple_documents():
    from apps.chat.models import Conversation, ConversationDocument
    from apps.documents.models import Document

    conversation = Conversation.objects.create(title="Chat 1", provider="mock", model="mock-1", status="ready")
    first = Document.objects.create(
        title="A",
        original_filename="a.txt",
        file_path="media/a.txt",
        mime_type="text/plain",
        size_bytes=1,
        source="upload",
        status="indexed",
        processing_status="indexed",
        summary_status="ready",
    )
    second = Document.objects.create(
        title="B",
        original_filename="b.txt",
        file_path="media/b.txt",
        mime_type="text/plain",
        size_bytes=1,
        source="upload",
        status="indexed",
        processing_status="indexed",
        summary_status="ready",
    )

    ConversationDocument.objects.create(conversation=conversation, document=first)
    ConversationDocument.objects.create(conversation=conversation, document=second)

    assert conversation.documents.count() == 2
