from django.db import transaction

from apps.documents.models import Document
from apps.jobs.tasks.conversation_tasks import prepare_conversation

from ..models import Conversation, ConversationDocument


class ConversationService:
    def create_conversation(self, payload):
        document_ids = payload.pop("document_ids", [])
        documents = list(Document.objects.filter(id__in=document_ids))
        status = (
            Conversation.Status.READY
            if documents and all(doc.processing_status == Document.Status.INDEXED for doc in documents)
            else Conversation.Status.PREPARING
        )

        with transaction.atomic():
            conversation = Conversation.objects.create(status=status, **payload)
            ConversationDocument.objects.bulk_create(
                [ConversationDocument(conversation=conversation, document=document) for document in documents]
            )
        prepare_conversation.delay(conversation.id)
        return conversation

    def replace_documents(self, conversation, document_ids):
        documents = list(Document.objects.filter(id__in=document_ids))
        conversation.documents.clear()
        ConversationDocument.objects.bulk_create(
            [ConversationDocument(conversation=conversation, document=document) for document in documents]
        )
        return conversation
