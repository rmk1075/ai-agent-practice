import os

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from typing import cast

from openai.types.responses import ResponseInputParam

from conversation.models import Conversation, Message
from conversation.serializers import ConversationDetailSerializer, ConversationSerializer, MessageSerializer
from conversation.service import OpenAIClient


openai_client = OpenAIClient()

SYSTEM_PROMPT = "You are a helpful assistant."
HISTORY_LIMIT = int(os.environ.get("CONVERSATION_HISTORY_LIMIT", 20))


class ConversationView(APIView):

    def get(self, request):
        conversations = Conversation.objects.filter(is_deleted=False).order_by('-created_at')
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):

    def _get_conversation(self, conversation_id):
        try:
            return Conversation.objects.get(id=conversation_id, is_deleted=False)
        except Conversation.DoesNotExist:
            return None

    def get(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConversationDetailSerializer(conversation)
        return Response(serializer.data)

    def patch(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConversationSerializer(conversation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationMessagesView(APIView):

    def _conversation_exists(self, conversation_id) -> bool:
        return Conversation.objects.filter(id=conversation_id, is_deleted=False).exists()

    def _build_messages(self, conversation_id, user_message) -> ResponseInputParam:
        # 최근 HISTORY_LIMIT개를 역순으로 가져온 뒤 시간순으로 되돌림
        history = list(
            Message.objects.filter(conversation_id=conversation_id)
            .exclude(id=user_message.id)
            .order_by('-created_at')[:HISTORY_LIMIT]
        )[::-1]

        return cast(ResponseInputParam, [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[{"role": m.role, "content": m.content} for m in history],
            {"role": "user", "content": user_message.content},
        ])

    def _stream_response(self, conversation_id, messages):
        ai_content = ""
        for delta in openai_client.stream(messages):
            ai_content += delta
            yield f"data: {delta}\n\n".encode()

        Message.objects.create(
            conversation_id=conversation_id,
            role='assistant',
            content=ai_content.strip(),
        )
        yield b"data: [DONE]\n\n"

    def get(self, request, conversation_id):
        if not self._conversation_exists(conversation_id):
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(conversation_id=conversation_id).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, conversation_id):
        if not self._conversation_exists(conversation_id):
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.save(conversation_id=conversation_id)

        messages = self._build_messages(conversation_id, user_message)
        return StreamingHttpResponse(self._stream_response(conversation_id, messages), content_type="text/event-stream")
