from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from conversation.models import Conversation
from conversation.serializers import ConversationDetailSerializer, ConversationSerializer


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
