from django.db import models

from agent.models import BaseModel


class Conversation(BaseModel):
    name = models.CharField(max_length=255)
    system_prompt = models.TextField(default="You are a helpful assistant.")
    model = models.CharField(max_length=100, default="gpt-4o-mini")
    temperature = models.FloatField(default=0.7)


class ConversationMetadata(BaseModel):
    key = models.CharField(max_length=255)
    value = models.TextField()

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="metadata"
    )


class Role(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class Message(BaseModel):
    role = models.CharField(max_length=255, choices=Role.choices)
    content = models.TextField(blank=True, default="")

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )


class ConversationMessageFile(BaseModel):
    message = models.OneToOneField(
        Message, on_delete=models.CASCADE, related_name="file"
    )
    filename = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
