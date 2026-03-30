from django.db import models

from agent.models import BaseModel


class Conversation(BaseModel):
    name = models.CharField(max_length=255)


class ConversationMetadata(BaseModel):
    key = models.CharField(max_length=255)
    value = models.TextField()

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='metadata')


class Role(models.TextChoices):
    USER = 'user', 'User'
    ASSISTANT = 'assistant', 'Assistant'
    SYSTEM = 'system', 'System'


class Message(BaseModel):
    role = models.CharField(max_length=255, choices=Role.choices)
    content = models.TextField()

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
