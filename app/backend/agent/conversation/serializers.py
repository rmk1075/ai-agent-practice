from rest_framework import serializers

from conversation.models import Conversation, ConversationMetadata, Message


class ConversationMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMetadata
        fields = ['key', 'value']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'name', 'created_at', 'updated_at']


class ConversationDetailSerializer(serializers.ModelSerializer):
    metadata = ConversationMetadataSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'created_at', 'updated_at', 'metadata']
