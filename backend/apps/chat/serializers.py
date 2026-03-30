from rest_framework import serializers

from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    document_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Conversation
        fields = ("id", "title", "provider", "model", "system_prompt", "status", "document_ids", "created_at", "updated_at")
        read_only_fields = ("status", "created_at", "updated_at")


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "role",
            "content",
            "provider",
            "model",
            "tokens_input",
            "tokens_output",
            "latency_ms",
            "metadata_json",
            "created_at",
        )
        read_only_fields = ("provider", "model", "tokens_input", "tokens_output", "latency_ms", "metadata_json", "created_at")


class ConversationStatusSerializer(serializers.ModelSerializer):
    ready_for_chat = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "status", "ready_for_chat")

    def get_ready_for_chat(self, obj):
        return obj.status == Conversation.Status.READY
