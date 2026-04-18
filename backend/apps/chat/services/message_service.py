from rest_framework import status
from django.conf import settings

from apps.llm.services.completion_service import CompletionService
from apps.retrieval.services.search_service import SearchService

from ..models import Conversation, Message
from .session_memory import SessionMemoryStore


class MessageService:
    def __init__(self, search_service=None, completion_service=None, session_memory=None):
        self.search_service = search_service or SearchService()
        self.completion_service = completion_service or CompletionService()
        self.max_turns = int(getattr(settings, "SESSION_MEMORY_MAX_TURNS", 8))
        self.memory_enabled = bool(getattr(settings, "SESSION_MEMORY_ENABLED", True))
        self.session_memory = session_memory or SessionMemoryStore(max_turns=self.max_turns)

    def send_message(self, conversation_id, payload):
        conversation = Conversation.objects.get(pk=conversation_id)
        if conversation.status != Conversation.Status.READY:
            return {"status": conversation.status, "ready_for_chat": False}, status.HTTP_409_CONFLICT

        content = (payload.get("content", "") or "").strip()
        if not content:
            return {"message": "Content is required."}, status.HTTP_400_BAD_REQUEST

        history = self._get_chat_history(conversation)
        user_message = Message.objects.create(conversation=conversation, role=Message.Role.USER, content=content)
        document_ids = list(conversation.documents.values_list("id", flat=True))
        hits = self.search_service.search(query=content, document_ids=document_ids, limit=getattr(settings, "RETRIEVAL_TOP_K", 5))
        try:
            response = self.completion_service.generate(
                provider=conversation.provider,
                model=conversation.model,
                prompt=content,
                context_hits=hits,
                chat_history=history,
                system_prompt=conversation.system_prompt,
            )
        except Exception as exc:
            return {
                "message": f"LLM provider '{conversation.provider}' is unavailable: {exc}",
                "provider": conversation.provider,
                "model": conversation.model,
            }, status.HTTP_502_BAD_GATEWAY
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=response["content"],
            provider=response["provider"],
            model=response["model"],
            tokens_input=response.get("tokens_input", 0),
            tokens_output=response.get("tokens_output", 0),
            latency_ms=response.get("latency_ms", 0),
            metadata_json={"hits": hits, "history_size": len(history)},
        )
        if self.memory_enabled:
            self.session_memory.append_turn(conversation.id, content, response["content"])

        return {
            "user_message": {"id": user_message.id, "content": user_message.content},
            "assistant_message": {
                "id": assistant_message.id,
                "content": assistant_message.content,
                "provider": assistant_message.provider,
                "model": assistant_message.model,
                "latency_ms": assistant_message.latency_ms,
            },
            "hits": hits,
        }, status.HTTP_201_CREATED

    def _get_chat_history(self, conversation):
        db_history = self._load_recent_history_from_db(conversation)
        if not db_history:
            self.session_memory.clear_session(conversation.id)
            return []

        if not self.memory_enabled:
            return db_history

        memory_history = self.session_memory.get_history(conversation.id)
        if not memory_history:
            self.session_memory.set_history(conversation.id, db_history)
            return db_history

        if len(memory_history) != len(db_history) or memory_history[-1].get("content") != db_history[-1].get("content"):
            self.session_memory.set_history(conversation.id, db_history)
            return db_history

        return memory_history

    def _load_recent_history_from_db(self, conversation):
        messages = list(
            Message.objects.filter(conversation=conversation, role__in=[Message.Role.USER, Message.Role.ASSISTANT])
            .order_by("-created_at")[: self.max_turns * 2]
        )
        messages.reverse()
        return [{"role": message.role, "content": message.content} for message in messages]
