from django.db import models


class Conversation(models.Model):
    class Status(models.TextChoices):
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=50, default="mock")
    model = models.CharField(max_length=100, default="mock-1")
    system_prompt = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PREPARING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    documents = models.ManyToManyField("documents.Document", through="ConversationDocument", related_name="conversations")


class ConversationDocument(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    document = models.ForeignKey("documents.Document", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("conversation", "document")


class Message(models.Model):
    class Role(models.TextChoices):
        SYSTEM = "system", "System"
        ASSISTANT = "assistant", "Assistant"
        USER = "user", "User"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    provider = models.CharField(max_length=50, blank=True, default="")
    model = models.CharField(max_length=100, blank=True, default="")
    tokens_input = models.PositiveIntegerField(default=0)
    tokens_output = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
