from unittest.mock import MagicMock, patch

from conversation.models import Conversation, ConversationMetadata, Message
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient


class ConversationViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/conversations/"

    def test_get_conversations_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_conversations(self):
        conv1 = Conversation.objects.create(name="conv1")
        conv2 = Conversation.objects.create(name="conv2")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertTrue(any(c["id"] == conv1.id for c in response.json()))
        self.assertTrue(any(c["id"] == conv2.id for c in response.json()))

    def test_get_conversations_excludes_deleted(self):
        active = Conversation.objects.create(name="active")
        deleted = Conversation.objects.create(name="deleted")
        deleted.delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], active.id)

    def test_post_conversation(self):
        response = self.client.post(self.url, {"name": "new conv"}, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "new conv")
        self.assertTrue(Conversation.objects.filter(id=data["id"]).exists())

    def test_post_conversation_missing_name(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_conversation_with_ai_settings(self):
        response = self.client.post(
            self.url,
            {
                "name": "창의적 대화",
                "model": "gpt-4o",
                "temperature": 1.0,
                "system_prompt": "You are a creative writer.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["model"], "gpt-4o")
        self.assertEqual(data["temperature"], 1.0)
        self.assertEqual(data["system_prompt"], "You are a creative writer.")

    def test_post_conversation_uses_defaults(self):
        response = self.client.post(self.url, {"name": "기본 대화"}, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["model"], "gpt-4o-mini")
        self.assertAlmostEqual(data["temperature"], 0.7)
        self.assertEqual(data["system_prompt"], "You are a helpful assistant.")

    def test_patch_conversation_system_prompt(self):
        conv = Conversation.objects.create(name="test")
        response = self.client.patch(
            f"/conversations/{conv.id}/",
            {"system_prompt": "You are a Python expert."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["system_prompt"], "You are a Python expert.")


class ConversationDetailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.conversation = Conversation.objects.create(name="test conv")
        self.url = f"/conversations/{self.conversation.id}/"

    def test_get_conversation(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.conversation.id)
        self.assertEqual(data["name"], "test conv")
        self.assertIn("metadata", data)

    def test_get_conversation_with_metadata(self):
        created = ConversationMetadata.objects.create(
            conversation=self.conversation, key="model", value="gpt-4"
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        metadata = response.json()["metadata"]
        self.assertEqual(len(metadata), 1)
        self.assertEqual(metadata[0]["key"], created.key)
        self.assertEqual(metadata[0]["value"], created.value)

    def test_get_conversation_not_found(self):
        response = self.client.get("/conversations/9999/")
        self.assertEqual(response.status_code, 404)

    def test_get_conversation_deleted(self):
        self.conversation.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_patch_conversation_name(self):
        response = self.client.patch(self.url, {"name": "updated name"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "updated name")
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.name, "updated name")

    def test_patch_conversation_not_found(self):
        response = self.client.patch(
            "/conversations/9999/", {"name": "x"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_conversation(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.is_deleted)

    def test_delete_conversation_not_found(self):
        response = self.client.delete("/conversations/9999/")
        self.assertEqual(response.status_code, 404)


class ConversationMessagesViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.conversation = Conversation.objects.create(name="test conv")
        self.url = f"/conversations/{self.conversation.id}/messages/"

    def test_get_messages_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_messages(self):
        msg1 = Message.objects.create(
            conversation=self.conversation, role="user", content="hello"
        )
        msg2 = Message.objects.create(
            conversation=self.conversation, role="assistant", content="hi"
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertTrue(any(m["id"] == msg1.pk for m in data))
        self.assertTrue(any(m["id"] == msg2.pk for m in data))

    def test_get_messages_returns_correct_fields(self):
        Message.objects.create(
            conversation=self.conversation, role="user", content="hello"
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        msg = response.json()[0]
        self.assertIn("id", msg)
        self.assertIn("role", msg)
        self.assertIn("content", msg)
        self.assertIn("created_at", msg)

    def test_get_messages_ordered_by_created_at(self):
        msg1 = Message.objects.create(
            conversation=self.conversation, role="user", content="first"
        )
        msg2 = Message.objects.create(
            conversation=self.conversation, role="assistant", content="second"
        )

        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(data[0]["id"], msg1.pk)
        self.assertEqual(data[1]["id"], msg2.pk)

    def test_get_messages_only_from_target_conversation(self):
        other_conv = Conversation.objects.create(name="other conv")
        Message.objects.create(
            conversation=self.conversation, role="user", content="mine"
        )
        Message.objects.create(conversation=other_conv, role="user", content="not mine")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["content"], "mine")

    def test_get_messages_conversation_not_found(self):
        response = self.client.get("/conversations/9999/messages/")
        self.assertEqual(response.status_code, 404)

    def test_get_messages_conversation_deleted(self):
        self.conversation.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @patch("conversation.views.ConversationGraph")
    def test_post_message(self, mock_graph_cls):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])
        response = self.client.post(
            self.url, {"role": "user", "content": "hello"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        b"".join(response.streaming_content)
        self.assertTrue(
            Message.objects.filter(
                role="user", content="hello", conversation=self.conversation
            ).exists()
        )

    @patch("conversation.views.ConversationGraph")
    def test_post_message_assistant_role(self, mock_graph_cls):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])
        response = self.client.post(
            self.url, {"role": "assistant", "content": "hi"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        b"".join(response.streaming_content)
        self.assertTrue(
            Message.objects.filter(
                role="assistant", content="hi", conversation=self.conversation
            ).exists()
        )

    def test_post_message_missing_role(self):
        response = self.client.post(self.url, {"content": "hello"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_message_invalid_role(self):
        response = self.client.post(
            self.url, {"role": "invalid", "content": "hello"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_post_message_conversation_not_found(self):
        response = self.client.post(
            "/conversations/9999/messages/",
            {"role": "user", "content": "hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_post_message_conversation_deleted(self):
        self.conversation.delete()
        response = self.client.post(
            self.url, {"role": "user", "content": "hello"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    @patch("conversation.views.ConversationGraph")
    def test_post_message_includes_system_prompt_in_stream(self, mock_graph_cls):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])

        self.conversation.system_prompt = "Be concise."
        self.conversation.save()

        response = self.client.post(
            self.url, {"role": "user", "content": "hello"}, format="json"
        )
        b"".join(response.streaming_content)

        _, kwargs = mock_graph_cls.call_args
        self.assertEqual(kwargs["system_prompt"], "Be concise.")

    @patch("conversation.views.ConversationGraph")
    def test_post_message_includes_history_in_stream(self, mock_graph_cls):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])

        Message.objects.create(
            conversation=self.conversation, role="user", content="first msg"
        )
        Message.objects.create(
            conversation=self.conversation, role="assistant", content="first reply"
        )

        response = self.client.post(
            self.url, {"role": "user", "content": "second msg"}, format="json"
        )
        b"".join(response.streaming_content)

        history, user_content, _ = mock_graph.stream.call_args[0]
        history_contents = [m.content for m in history]
        self.assertIn("first msg", history_contents)
        self.assertIn("first reply", history_contents)
        self.assertEqual(user_content, "second msg")

    @patch("conversation.views.HISTORY_LIMIT", 2)
    @patch("conversation.views.ConversationGraph")
    def test_post_message_respects_history_limit(self, mock_graph_cls):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])

        for i in range(5):
            Message.objects.create(
                conversation=self.conversation, role="user", content=f"msg {i}"
            )

        response = self.client.post(
            self.url, {"role": "user", "content": "new msg"}, format="json"
        )
        b"".join(response.streaming_content)

        history, *_ = mock_graph.stream.call_args[0]
        self.assertEqual(len(history), 2)

    @patch("conversation.views.ConversationGraph")
    def test_post_message_current_user_message_not_duplicated_in_history(
        self, mock_graph_cls
    ):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])

        response = self.client.post(
            self.url, {"role": "user", "content": "my message"}, format="json"
        )
        b"".join(response.streaming_content)

        history, user_content, _ = mock_graph.stream.call_args[0]
        self.assertEqual(user_content, "my message")
        history_contents = [m.content for m in history]
        self.assertNotIn("my message", history_contents)

    @patch("conversation.views.ConversationGraph")
    def test_post_message_passes_conversation_id_to_stream(self, mock_graph_cls):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])

        response = self.client.post(
            self.url, {"role": "user", "content": "hello"}, format="json"
        )
        b"".join(response.streaming_content)

        _, user_content, conversation_id = mock_graph.stream.call_args[0]
        self.assertEqual(conversation_id, self.conversation.id)

    def test_post_message_no_content_no_file_returns_400(self):
        response = self.client.post(self.url, {"role": "user"}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"], "Either content or file must be provided."
        )

    def test_post_message_whitespace_only_content_no_file_returns_400(self):
        response = self.client.post(
            self.url, {"role": "user", "content": "   "}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"], "Either content or file must be provided."
        )

    @patch("conversation.views.FileParser")
    @patch("conversation.views.ConversationGraph")
    def test_post_message_file_only_saves_parsed_content(
        self, mock_graph_cls, mock_parser_cls
    ):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])
        mock_parser = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_parser.parse.return_value = "parsed file text"

        pdf = SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(
            self.url, {"role": "user", "file": pdf, "path": "test-uuid-pdf"}, format="multipart"
        )
        self.assertEqual(response.status_code, 200)
        b"".join(response.streaming_content)
        self.assertTrue(
            Message.objects.filter(
                role="user",
                content="",
                conversation=self.conversation,
            ).exists()
        )

    @patch("conversation.views.FileParser")
    @patch("conversation.views.ConversationGraph")
    def test_post_message_docx_file_only_saves_parsed_content(
        self, mock_graph_cls, mock_parser_cls
    ):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])
        mock_parser = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_parser.parse.return_value = "parsed docx text"

        docx = SimpleUploadedFile(
            "report.docx",
            b"PK",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response = self.client.post(
            self.url, {"role": "user", "file": docx, "path": "test-uuid-docx"}, format="multipart"
        )
        self.assertEqual(response.status_code, 200)
        b"".join(response.streaming_content)
        self.assertTrue(
            Message.objects.filter(
                role="user",
                content="",
                conversation=self.conversation,
            ).exists()
        )

    @patch("conversation.views.FileParser")
    @patch("conversation.views.ConversationGraph")
    def test_post_message_content_and_file_merges_both(
        self, mock_graph_cls, mock_parser_cls
    ):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])
        mock_parser = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_parser.parse.return_value = "parsed file text"

        pdf = SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(
            self.url,
            {"role": "user", "content": "my question", "file": pdf, "path": "test-uuid-merge"},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        b"".join(response.streaming_content)
        self.assertTrue(
            Message.objects.filter(
                role="user",
                content="my question",
                conversation=self.conversation,
            ).exists()
        )

    @patch("conversation.views.FileParser")
    def test_post_message_unsupported_file_type_returns_400(self, mock_parser_cls):
        from conversation.file_parser import UnsupportedFileTypeError

        mock_parser = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_parser.parse.side_effect = UnsupportedFileTypeError("unsupported")

        txt = SimpleUploadedFile("doc.txt", b"hello", content_type="text/plain")
        response = self.client.post(
            self.url, {"role": "user", "file": txt, "path": "test-uuid-unsupported"}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Unsupported file type. Only PDF and DOCX are allowed.",
        )

    @patch("conversation.views.FileParser")
    def test_post_message_file_too_large_returns_400(self, mock_parser_cls):
        from conversation.file_parser import FileTooLargeError

        mock_parser = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_parser.parse.side_effect = FileTooLargeError("too large")

        pdf = SimpleUploadedFile("big.pdf", b"x", content_type="application/pdf")
        response = self.client.post(
            self.url, {"role": "user", "file": pdf, "path": "test-uuid-toolarge"}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"], "File size exceeds limit of 10MB."
        )

    @patch("conversation.views.FileParser")
    def test_post_message_parse_failure_returns_400(self, mock_parser_cls):
        from conversation.file_parser import FileParseError

        mock_parser = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_parser.parse.side_effect = FileParseError("failed")

        pdf = SimpleUploadedFile("bad.pdf", b"corrupt", content_type="application/pdf")
        response = self.client.post(
            self.url, {"role": "user", "file": pdf, "path": "test-uuid-parsefail"}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Failed to parse file.")

    @patch("conversation.views.FileParser")
    @patch("conversation.views.ConversationGraph")
    def test_post_message_merged_content_passed_to_stream(
        self, mock_graph_cls, mock_parser_cls
    ):
        mock_graph = MagicMock()
        mock_graph_cls.return_value = mock_graph
        mock_graph.stream.return_value = iter([])
        mock_parser = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_parser.parse.return_value = "file content"

        pdf = SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = self.client.post(
            self.url,
            {"role": "user", "content": "question", "file": pdf, "path": "test-uuid-stream"},
            format="multipart",
        )
        b"".join(response.streaming_content)

        _, user_content, _ = mock_graph.stream.call_args[0]
        self.assertEqual(user_content, "question\n\n[File: doc.pdf]\nfile content")

    def test_post_with_file_but_no_path_returns_400(self):
        pdf_content = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"
        file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        data = {"role": "user", "content": "analyze this", "file": file}
        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(response.status_code, 400)

    @patch("conversation.views.FileParser")
    @patch("conversation.views.ConversationGraph")
    def test_post_with_file_stores_only_user_text_in_message_content(self, MockGraph, MockParser):
        MockGraph.return_value.stream.return_value = iter(["ok"])
        MockParser.return_value.parse.return_value = "parsed content"
        pdf_content = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"
        file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        data = {
            "role": "user",
            "content": "analyze this",
            "file": file,
            "path": "test-uuid-001",
        }
        self.client.post(self.url, data=data, format="multipart")
        message = Message.objects.filter(role="user").last()
        self.assertEqual(message.content, "analyze this")
        self.assertNotIn("[File:", message.content)

    @patch("conversation.views.FileParser")
    @patch("conversation.views.ConversationGraph")
    def test_post_with_file_creates_conversation_message_file(self, MockGraph, MockParser):
        from conversation.models import ConversationMessageFile
        MockGraph.return_value.stream.return_value = iter(["ok"])
        MockParser.return_value.parse.return_value = "parsed content"
        pdf_content = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"
        file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        data = {
            "role": "user",
            "content": "analyze this",
            "file": file,
            "path": "test-uuid-002",
        }
        self.client.post(self.url, data=data, format="multipart")
        message = Message.objects.filter(role="user").last()
        cmf = ConversationMessageFile.objects.get(message=message)
        self.assertEqual(cmf.filename, "test.pdf")
        self.assertEqual(cmf.path, "test-uuid-002")

    @patch("conversation.views.FileParser")
    @patch("conversation.views.ConversationGraph")
    def test_post_file_only_with_no_content_saves_empty_string(self, MockGraph, MockParser):
        MockGraph.return_value.stream.return_value = iter(["ok"])
        MockParser.return_value.parse.return_value = "parsed content"
        pdf_content = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"
        file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        data = {"role": "user", "file": file, "path": "test-uuid-003"}
        self.client.post(self.url, data=data, format="multipart")
        message = Message.objects.filter(role="user").last()
        self.assertEqual(message.content, "")

    def test_get_messages_includes_file_info_when_file_attached(self):
        from conversation.models import ConversationMessageFile
        message = Message.objects.create(
            conversation=self.conversation, role="user", content="analyze this"
        )
        ConversationMessageFile.objects.create(
            message=message, filename="doc.pdf", path="uuid-abc-123"
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        user_msg = next(m for m in response.data if m["role"] == "user")
        self.assertIsNotNone(user_msg["file"])
        self.assertEqual(user_msg["file"]["filename"], "doc.pdf")
        self.assertEqual(user_msg["file"]["path"], "uuid-abc-123")

    def test_get_messages_file_is_null_when_no_file_attached(self):
        Message.objects.create(
            conversation=self.conversation, role="user", content="hello"
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        user_msg = next(m for m in response.data if m["role"] == "user")
        self.assertIsNone(user_msg["file"])
