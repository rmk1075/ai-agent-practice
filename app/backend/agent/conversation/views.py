import os

from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from conversation.file_parser import (
    FileParseError,
    FileParser,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from conversation.models import Conversation, ConversationMessageFile, Message
from conversation.serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
    MessageSerializer,
)
from conversation.service import ConversationGraph

HISTORY_LIMIT = int(os.environ.get("CONVERSATION_HISTORY_LIMIT", 20))


class ConversationView(APIView):
    def get(self, request):
        conversations = Conversation.objects.filter(is_deleted=False).order_by(
            "-created_at"
        )
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
            return Response(
                {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ConversationDetailSerializer(conversation)
        return Response(serializer.data)

    def patch(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return Response(
                {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ConversationSerializer(
            conversation, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return Response(
                {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
            )

        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationMessagesView(APIView):
    def _get_conversation(self, conversation_id):
        try:
            return Conversation.objects.get(id=conversation_id, is_deleted=False)
        except Conversation.DoesNotExist:
            return None

    def _get_history(self, conversation_id, exclude_id):
        return list(
            Message.objects.filter(conversation_id=conversation_id)
            .exclude(id=exclude_id)
            .order_by("-created_at")[:HISTORY_LIMIT]
        )[::-1]

    def _stream_response(self, conversation_id, graph, history, user_message: str):
        ai_content = ""
        try:
            for delta in graph.stream(history, user_message, conversation_id):
                ai_content += delta
                yield f"data: {delta}\n\n".encode()
        except Exception:
            if not ai_content:
                ai_content = "[error]"
        finally:
            Message.objects.create(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_content.strip(),
            )
        yield b"data: [DONE]\n\n"

    def get(self, request, conversation_id):
        if self._get_conversation(conversation_id) is None:
            return Response(
                {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
            )

        messages = Message.objects.filter(conversation_id=conversation_id).order_by(
            "created_at"
        )
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return Response(
                {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
            )

        content = request.data.get("content", "").strip()
        file = request.FILES.get("file")
        path = request.data.get("path")

        if not content and file is None:
            return Response(
                {"error": "Either content or file must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file and not path:
            return Response(
                {"error": "path is required when file is provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        llm_content = content
        if file:
            try:
                parsed_text = FileParser().parse(file)
            except FileTooLargeError:
                return Response(
                    {"error": "File size exceeds limit of 10MB."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except UnsupportedFileTypeError:
                return Response(
                    {"error": "Unsupported file type. Only PDF and DOCX are allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except FileParseError:
                return Response(
                    {"error": "Failed to parse file."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            safe_name = file.name.replace("\n", " ").replace("]", "")
            file_section = f"[File: {safe_name}]\n{parsed_text}"
            llm_content = f"{content}\n\n{file_section}" if content else file_section

        serializer = MessageSerializer(
            data={"role": request.data.get("role"), "content": content}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user_message = serializer.save(conversation_id=conversation_id)
            if file:
                ConversationMessageFile.objects.create(
                    message=user_message,
                    filename=file.name,
                    path=path,
                )

        graph = ConversationGraph(
            model=conversation.model,
            temperature=conversation.temperature,
            system_prompt=conversation.system_prompt,
        )
        history = self._get_history(conversation_id, exclude_id=user_message.id)
        return StreamingHttpResponse(
            self._stream_response(conversation_id, graph, history, llm_content),
            content_type="text/event-stream",
        )
