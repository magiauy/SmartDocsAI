from celery import shared_task

from apps.chat.models import Conversation, Message
from apps.documents.models import Document


@shared_task
def prepare_conversation(conversation_id: int):
    conversation = Conversation.objects.get(pk=conversation_id)
    documents = list(conversation.documents.all())
    if documents and all(doc.processing_status == Document.Status.INDEXED for doc in documents):
        summary = "\n".join(filter(None, [doc.summary for doc in documents])) or f"{len(documents)} document(s) ready."
        Message.objects.get_or_create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            defaults={"content": summary, "provider": conversation.provider, "model": conversation.model},
        )
        conversation.status = Conversation.Status.READY
    else:
        conversation.status = Conversation.Status.PREPARING
    conversation.save(update_fields=["status", "updated_at"])
