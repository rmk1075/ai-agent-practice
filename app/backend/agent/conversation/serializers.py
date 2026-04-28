from rest_framework import serializers

from conversation.models import Conversation, ConversationMessageFile, ConversationMetadata, Message


class ConversationMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMetadata
        fields = ["key", "value"]


class ConversationMessageFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMessageFile
        fields = ["id", "filename", "path"]


class MessageSerializer(serializers.ModelSerializer):
    file = ConversationMessageFileSerializer(read_only=True, default=None)

    class Meta:
        model = Message
        fields = ["id", "role", "content", "file", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "id",
            "name",
            "system_prompt",
            "model",
            "temperature",
            "created_at",
            "updated_at",
        ]


class ConversationDetailSerializer(serializers.ModelSerializer):
    metadata = ConversationMetadataSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "name",
            "system_prompt",
            "model",
            "temperature",
            "created_at",
            "updated_at",
            "metadata",
        ]
