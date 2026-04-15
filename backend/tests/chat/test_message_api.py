import pytest


@pytest.mark.django_db
def test_send_message_persists_user_and_assistant_messages(api_client, mocker):
    from apps.chat.models import Conversation, ConversationDocument, Message
    from apps.documents.models import Document

    document = Document.objects.create(
        title="Indexed",
        original_filename="indexed.txt",
        file_path="media/indexed.txt",
        mime_type="text/plain",
        size_bytes=10,
        source="upload",
        status="indexed",
        processing_status="indexed",
        summary_status="ready",
    )
    conversation = Conversation.objects.create(title="Ready", provider="mock", model="mock-1", status="ready")
    ConversationDocument.objects.create(conversation=conversation, document=document)

    mocker.patch(
        "apps.chat.services.message_service.SearchService.search",
        return_value=[{"content": "doc context", "score": 0.9, "metadata": {"document_id": document.id}}],
    )
    mocker.patch(
        "apps.chat.services.message_service.CompletionService.generate",
        return_value={
            "provider": "mock",
            "model": "mock-1",
            "content": "assistant answer",
            "tokens_input": 10,
            "tokens_output": 20,
            "latency_ms": 5,
        },
    )

    response = api_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {"content": "What is this?", "role": "user"},
        format="json",
    )

    assert response.status_code == 201
    assert Message.objects.filter(conversation=conversation).count() == 2
    payload = response.json()["data"]
    assert payload["assistant_message"]["content"] == "assistant answer"


@pytest.mark.django_db
def test_send_message_returns_guard_response_for_preparing_conversation(api_client):
    from apps.chat.models import Conversation

    conversation = Conversation.objects.create(title="Preparing", provider="mock", model="mock-1", status="preparing")

    response = api_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {"content": "Hello", "role": "user"},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["data"]["ready_for_chat"] is False


@pytest.mark.django_db
def test_send_message_rejects_blank_content(api_client):
    from apps.chat.models import Conversation, ConversationDocument
    from apps.documents.models import Document

    document = Document.objects.create(
        title="Indexed",
        original_filename="indexed.txt",
        file_path="media/indexed.txt",
        mime_type="text/plain",
        size_bytes=10,
        source="upload",
        status="indexed",
        processing_status="indexed",
        summary_status="ready",
    )
    conversation = Conversation.objects.create(title="Ready", provider="mock", model="mock-1", status="ready")
    ConversationDocument.objects.create(conversation=conversation, document=document)

    response = api_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {"content": "   ", "role": "user"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["data"]["message"] == "Content is required."


@pytest.mark.django_db
def test_send_message_uses_in_memory_session_history(api_client, mocker):
    from apps.chat.models import Conversation, ConversationDocument
    from apps.documents.models import Document

    document = Document.objects.create(
        title="Indexed",
        original_filename="indexed.txt",
        file_path="media/indexed.txt",
        mime_type="text/plain",
        size_bytes=10,
        source="upload",
        status="indexed",
        processing_status="indexed",
        summary_status="ready",
    )
    conversation = Conversation.objects.create(title="Ready", provider="mock", model="mock-1", status="ready")
    ConversationDocument.objects.create(conversation=conversation, document=document)

    mocker.patch(
        "apps.chat.services.message_service.SearchService.search",
        return_value=[{"content": "doc context", "score": 0.9, "metadata": {"document_id": document.id}}],
    )
    completion_mock = mocker.patch(
        "apps.chat.services.message_service.CompletionService.generate",
        side_effect=[
            {
                "provider": "mock",
                "model": "mock-1",
                "content": "assistant answer 1",
                "tokens_input": 10,
                "tokens_output": 20,
                "latency_ms": 5,
            },
            {
                "provider": "mock",
                "model": "mock-1",
                "content": "assistant answer 2",
                "tokens_input": 10,
                "tokens_output": 20,
                "latency_ms": 5,
            },
        ],
    )

    first = api_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {"content": "Question one", "role": "user"},
        format="json",
    )
    assert first.status_code == 201
    assert completion_mock.call_args_list[0].kwargs["chat_history"] == []

    second = api_client.post(
        f"/api/conversations/{conversation.id}/messages/",
        {"content": "Question two", "role": "user"},
        format="json",
    )
    assert second.status_code == 201
    second_history = completion_mock.call_args_list[1].kwargs["chat_history"]
    assert len(second_history) == 2
    assert second_history[0]["role"] == "user"
    assert second_history[1]["role"] == "assistant"
