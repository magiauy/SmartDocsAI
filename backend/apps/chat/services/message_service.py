from rest_framework import status

from apps.llm.services.completion_service import CompletionService
from apps.retrieval.services.search_service import SearchService

from ..models import Conversation, Message


class MessageService:
    def __init__(self, search_service=None, completion_service=None):
        self.search_service = search_service or SearchService()
        self.completion_service = completion_service or CompletionService()

    def send_message(self, conversation_id, payload):
        conversation = Conversation.objects.get(pk=conversation_id)
        if conversation.status != Conversation.Status.READY:
            return {"status": conversation.status, "ready_for_chat": False}, status.HTTP_409_CONFLICT

        content = payload.get("content", "")
        user_message = Message.objects.create(conversation=conversation, role=Message.Role.USER, content=content)
        document_ids = list(conversation.documents.values_list("id", flat=True))
        hits = self.search_service.search(query=content, document_ids=document_ids, limit=5)
        response = self.completion_service.generate(
            provider=conversation.provider,
            model=conversation.model,
            prompt=content,
            context_hits=hits,
        )
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=response["content"],
            provider=response["provider"],
            model=response["model"],
            tokens_input=response.get("tokens_input", 0),
            tokens_output=response.get("tokens_output", 0),
            latency_ms=response.get("latency_ms", 0),
            metadata_json={"hits": hits},
        )
        return {
            "user_message": {"id": user_message.id, "content": user_message.content},
            "assistant_message": {"id": assistant_message.id, "content": assistant_message.content},
            "hits": hits,
        }, status.HTTP_201_CREATED
