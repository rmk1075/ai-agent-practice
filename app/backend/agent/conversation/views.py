import random
import time

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from conversation.models import Conversation, Message
from conversation.serializers import ConversationDetailSerializer, ConversationSerializer, MessageSerializer
from conversation.service import OpenAIClient


openai_client = OpenAIClient()

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

    def _fake_agent_stream(self, message: str):
        text = f"AI response to: {message}"

        for token in text.split(" "):
            time.sleep(0.3)
            yield token + " "

        for i in range(random.randint(10, 20)):
            time.sleep(0.3)
            yield str(i) + " "


    def get(self, request, conversation_id):
        if not Conversation.objects.filter(id=conversation_id, is_deleted=False).exists():
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(conversation_id=conversation_id).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, conversation_id):
        if not Conversation.objects.filter(id=conversation_id, is_deleted=False).exists():
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.save(conversation_id=conversation_id)

        def event_stream():
            ai_content = ""
            for delta in openai_client.stream(user_message.content):
                ai_content += delta
                yield f"data: {delta}\n\n".encode()

            Message.objects.create(
                conversation_id=conversation_id,
                role='assistant',
                content=ai_content.strip(),
            )
            yield b"data: [DONE]\n\n"

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
