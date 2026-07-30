from unittest.mock import MagicMock, patch

from django.test import TestCase
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool
from langchain_core.tools import tool as lc_tool

from conversation import service
from conversation.models import Conversation, ConversationMetadata, Message
from conversation.service import ConversationGraph, extract_metadata


class ConversationGraphMetadataNodeTest(TestCase):
    @patch("conversation.service.ChatOpenAI")
    def test_metadata_node_formats_metadata_as_context(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()
        conv = Conversation.objects.create(name="test")
        ConversationMetadata.objects.create(
            conversation=conv, key="user_name", value="John"
        )
        ConversationMetadata.objects.create(
            conversation=conv, key="role", value="Lawyer"
        )

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
        )
        result = graph._metadata_node(
            {}, {"configurable": {"conversation_id": conv.id}}
        )

        self.assertEqual(
            result["metadata_context"],
            "\n\nContext:\n- user_name: John\n- role: Lawyer",
        )

    @patch("conversation.service.ChatOpenAI")
    def test_metadata_node_returns_empty_string_when_no_metadata(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()
        conv = Conversation.objects.create(name="test")

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
        )
        result = graph._metadata_node(
            {}, {"configurable": {"conversation_id": conv.id}}
        )

        self.assertEqual(result["metadata_context"], "")

    @patch("conversation.service.ChatOpenAI")
    def test_metadata_node_excludes_deleted_metadata(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()
        conv = Conversation.objects.create(name="test")
        ConversationMetadata.objects.create(
            conversation=conv, key="active_key", value="active_value"
        )
        deleted = ConversationMetadata.objects.create(
            conversation=conv, key="deleted_key", value="deleted_value"
        )
        deleted.delete()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
        )
        result = graph._metadata_node(
            {}, {"configurable": {"conversation_id": conv.id}}
        )

        self.assertIn("active_key", result["metadata_context"])
        self.assertIn("active_value", result["metadata_context"])
        self.assertNotIn("deleted_key", result["metadata_context"])


class ConversationGraphChatbotNodeTest(TestCase):
    @patch("conversation.service.ChatOpenAI")
    def test_chatbot_node_appends_metadata_context_to_system_prompt(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content="response")

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
        )
        state = {
            "messages": [HumanMessage(content="hello")],
            "metadata_context": "\n\nContext:\n- role: Lawyer",
        }
        graph._chatbot_node(state, {"configurable": {"conversation_id": 1}})

        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIsInstance(call_args[0], SystemMessage)
        self.assertEqual(
            call_args[0].content, "You are helpful.\n\nContext:\n- role: Lawyer"
        )

    @patch("conversation.service.ChatOpenAI")
    def test_chatbot_node_uses_system_prompt_only_when_no_metadata(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content="response")

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are a pirate.",
        )
        state = {
            "messages": [HumanMessage(content="hello")],
            "metadata_context": "",
        }
        graph._chatbot_node(state, {"configurable": {"conversation_id": 1}})

        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIsInstance(call_args[0], SystemMessage)
        self.assertEqual(call_args[0].content, "You are a pirate.")


class ConversationGraphStreamTest(TestCase):
    @patch("conversation.service.ChatOpenAI")
    def test_stream_yields_text_tokens(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        chunk1 = AIMessageChunk(content="Hello")
        chunk2 = AIMessageChunk(content=" world")
        empty_chunk = AIMessageChunk(content="")

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are a helpful assistant.",
        )

        with patch.object(
            graph._graph,
            "stream",
            return_value=iter([(chunk1, {}), (empty_chunk, {}), (chunk2, {})]),
        ):
            result = list(graph.stream([], "hi", 0))

        self.assertEqual(result, ["Hello", " world"])

    @patch("conversation.service.ChatOpenAI")
    def test_stream_skips_empty_chunks(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are a helpful assistant.",
        )

        empty = AIMessageChunk(content="")

        with patch.object(graph._graph, "stream", return_value=iter([(empty, {})])):
            result = list(graph.stream([], "hi", 0))

        self.assertEqual(result, [])

    @patch("conversation.service.ChatOpenAI")
    def test_stream_passes_history_as_messages(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="Be helpful.",
        )

        user_msg = MagicMock(spec=Message)
        user_msg.role = "user"
        user_msg.content = "first message"

        assistant_msg = MagicMock(spec=Message)
        assistant_msg.role = "assistant"
        assistant_msg.content = "first reply"

        captured = {}

        def fake_stream(input_dict, **kwargs):
            captured["input"] = input_dict
            return iter([])

        with patch.object(graph._graph, "stream", side_effect=fake_stream):
            list(graph.stream([user_msg, assistant_msg], "follow-up", 0))

        msgs = captured["input"]["messages"]
        self.assertEqual(len(msgs), 3)
        self.assertIsInstance(msgs[0], HumanMessage)
        self.assertEqual(msgs[0].content, "first message")
        self.assertIsInstance(msgs[1], AIMessage)
        self.assertEqual(msgs[1].content, "first reply")
        self.assertIsInstance(msgs[2], HumanMessage)
        self.assertEqual(msgs[2].content, "follow-up")

    @patch("conversation.service.ChatOpenAI")
    def test_stream_passes_empty_metadata_context_as_initial_state(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="Be helpful.",
        )

        captured = {}

        def fake_stream(input_dict, **kwargs):
            captured["input"] = input_dict
            return iter([])

        with patch.object(graph._graph, "stream", side_effect=fake_stream):
            list(graph.stream([], "hello", 0))

        self.assertEqual(captured["input"]["metadata_context"], "")


class ExtractMetadataTest(TestCase):
    @patch("conversation.service.ChatOpenAI")
    def test_extract_metadata_saves_new_metadata(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_extractor = MagicMock()
        mock_llm.with_structured_output.return_value = mock_extractor

        item1 = MagicMock()
        item1.key = "user_name"
        item1.value = "John"
        item2 = MagicMock()
        item2.key = "occupation"
        item2.value = "lawyer"
        extracted = MagicMock()
        extracted.items = [item1, item2]
        mock_extractor.invoke.return_value = extracted

        conv = Conversation.objects.create(name="test")

        extract_metadata(conv.id, "Hi, I'm John, a lawyer.")

        metas = ConversationMetadata.objects.filter(conversation=conv)
        self.assertEqual(metas.count(), 2)
        self.assertEqual(metas.get(key="user_name").value, "John")
        self.assertEqual(metas.get(key="occupation").value, "lawyer")

    @patch("conversation.service.ChatOpenAI")
    def test_extract_metadata_upserts_existing_key(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_extractor = MagicMock()
        mock_llm.with_structured_output.return_value = mock_extractor

        item = MagicMock()
        item.key = "user_name"
        item.value = "Jane"
        extracted = MagicMock()
        extracted.items = [item]
        mock_extractor.invoke.return_value = extracted

        conv = Conversation.objects.create(name="test")
        ConversationMetadata.objects.create(
            conversation=conv, key="user_name", value="John"
        )

        extract_metadata(conv.id, "Actually my name is Jane.")

        metas = ConversationMetadata.objects.filter(conversation=conv, key="user_name")
        self.assertEqual(metas.count(), 1)
        self.assertEqual(metas.first().value, "Jane")

    @patch("conversation.service.ChatOpenAI")
    def test_extract_metadata_skips_on_empty_result(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_extractor = MagicMock()
        mock_llm.with_structured_output.return_value = mock_extractor

        extracted = MagicMock()
        extracted.items = []
        mock_extractor.invoke.return_value = extracted

        conv = Conversation.objects.create(name="test")
        ConversationMetadata.objects.create(
            conversation=conv, key="existing_key", value="original_value"
        )

        extract_metadata(conv.id, "What's the weather like?")

        self.assertEqual(
            ConversationMetadata.objects.filter(conversation=conv).count(), 1
        )
        self.assertEqual(
            ConversationMetadata.objects.get(
                conversation=conv, key="existing_key"
            ).value,
            "original_value",
        )

    @patch("conversation.service.ChatOpenAI")
    def test_extract_metadata_handles_extractor_invoke_error_silently(
        self, mock_llm_cls
    ):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_extractor = MagicMock()
        mock_llm.with_structured_output.return_value = mock_extractor
        mock_extractor.invoke.side_effect = Exception("LLM unavailable")

        conv = Conversation.objects.create(name="test")

        try:
            extract_metadata(conv.id, "some message")
        except Exception:
            self.fail("extract_metadata raised an exception")

        self.assertEqual(
            ConversationMetadata.objects.filter(conversation=conv).count(), 0
        )

    @patch("conversation.service.ChatOpenAI")
    def test_extract_metadata_reactivates_soft_deleted_key(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_extractor = MagicMock()
        mock_llm.with_structured_output.return_value = mock_extractor

        item = MagicMock()
        item.key = "user_name"
        item.value = "Alice"
        extracted = MagicMock()
        extracted.items = [item]
        mock_extractor.invoke.return_value = extracted

        conv = Conversation.objects.create(name="test")
        meta = ConversationMetadata.objects.create(
            conversation=conv, key="user_name", value="Old"
        )
        meta.delete()  # soft delete

        extract_metadata(conv.id, "My name is Alice.")

        restored = ConversationMetadata.objects.get(conversation=conv, key="user_name")
        self.assertEqual(restored.value, "Alice")
        self.assertFalse(restored.is_deleted)


class ConversationGraphStreamThreadTest(TestCase):
    @patch("conversation.service.threading.Thread")
    @patch("conversation.service.ChatOpenAI")
    def test_stream_starts_extraction_thread_after_exhaustion(
        self, mock_llm_cls, mock_thread_cls
    ):
        mock_llm_cls.return_value = MagicMock()
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="Be helpful.",
        )

        with patch.object(graph._graph, "stream", return_value=iter([])):
            list(graph.stream([], "I'm Alice, a doctor.", 42))

        mock_thread_cls.assert_called_once_with(
            target=extract_metadata,
            args=(42, "I'm Alice, a doctor."),
            daemon=True,
        )
        mock_thread.start.assert_called_once()

    @patch("conversation.service.threading.Thread")
    @patch("conversation.service.ChatOpenAI")
    def test_stream_does_not_start_thread_when_generator_closed_early(
        self, mock_llm_cls, mock_thread_cls
    ):
        mock_llm_cls.return_value = MagicMock()
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="Be helpful.",
        )

        chunk = AIMessageChunk(content="Hello")

        with patch.object(graph._graph, "stream", return_value=iter([(chunk, {})])):
            gen = graph.stream([], "I'm Alice, a doctor.", 42)
            next(gen)  # consume one item
            gen.close()  # close before exhaustion

        mock_thread.start.assert_not_called()


class GetMcpToolsTest(TestCase):
    def tearDown(self):
        service._mcp_tools = None

    @patch("conversation.service.MultiServerMCPClient")
    def test_returns_empty_list_when_server_unreachable(self, mock_client_cls):
        service._mcp_tools = None
        mock_client_cls.side_effect = Exception("connection refused")

        self.assertEqual(service.get_mcp_tools(), [])

    @patch("conversation.service.MultiServerMCPClient")
    def test_wraps_async_tools_with_sync_func_and_caches(self, mock_client_cls):
        service._mcp_tools = None

        async def acall() -> str:
            return "ok"

        mcp_tool = StructuredTool(
            name="probe",
            description="probe",
            coroutine=acall,
            args_schema={"type": "object", "properties": {}},
        )

        async def fake_get_tools():
            return [mcp_tool]

        mock_client_cls.return_value.get_tools = fake_get_tools

        tools = service.get_mcp_tools()

        self.assertEqual(len(tools), 1)
        self.assertIsNotNone(tools[0].func)
        self.assertEqual(tools[0].func(), "ok")

        service.get_mcp_tools()
        self.assertEqual(mock_client_cls.call_count, 1)


class ConversationGraphToolLoopTest(TestCase):
    def _tool_call_message(self):
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "save_memory",
                    "args": {
                        "conversation_id": 42,
                        "key": "user_name",
                        "value": "John",
                    },
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        )

    @patch("conversation.service.ChatOpenAI")
    def test_graph_executes_tool_call_and_returns_final_answer(self, mock_llm_cls):
        calls = []

        @lc_tool
        def save_memory(conversation_id: int, key: str, value: str) -> str:
            """Save a memory."""
            calls.append((conversation_id, key, value))
            return "saved"

        bound_llm = MagicMock()
        bound_llm.invoke.side_effect = [
            self._tool_call_message(),
            AIMessage(content="done"),
        ]
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = bound_llm
        mock_llm_cls.return_value = mock_llm

        conv = Conversation.objects.create(name="test")
        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
            tools=[save_memory],
        )

        result = graph._graph.invoke(
            {"messages": [HumanMessage(content="I'm John")], "metadata_context": ""},
            config={"configurable": {"conversation_id": conv.id}},
        )

        self.assertEqual(calls, [(42, "user_name", "John")])
        self.assertEqual(result["messages"][-1].content, "done")

    @patch("conversation.service.ChatOpenAI")
    def test_chatbot_node_includes_tool_guidance_with_conversation_id(
        self, mock_llm_cls
    ):
        @lc_tool
        def save_memory(conversation_id: int, key: str, value: str) -> str:
            """Save a memory."""
            return "saved"

        bound_llm = MagicMock()
        bound_llm.invoke.return_value = AIMessage(content="hi")
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = bound_llm
        mock_llm_cls.return_value = mock_llm

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
            tools=[save_memory],
        )
        graph._chatbot_node(
            {"messages": [HumanMessage(content="hello")], "metadata_context": ""},
            {"configurable": {"conversation_id": 42}},
        )

        prompt = bound_llm.invoke.call_args[0][0][0].content
        self.assertIn("conversation_id is 42", prompt)
        self.assertIn("save_memory", prompt)

    @patch("conversation.service.ChatOpenAI")
    def test_chatbot_node_omits_tool_guidance_without_tools(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="hi")
        mock_llm_cls.return_value = mock_llm

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
        )
        graph._chatbot_node(
            {"messages": [HumanMessage(content="hello")], "metadata_context": ""},
            {"configurable": {"conversation_id": 42}},
        )

        prompt = mock_llm.invoke.call_args[0][0][0].content
        self.assertEqual(prompt, "You are helpful.")

    @patch("conversation.service.ChatOpenAI")
    def test_stream_skips_tool_messages(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
        )

        tool_msg = ToolMessage(content="saved: user_name", tool_call_id="call_1")
        ai_chunk = AIMessageChunk(content="Hello")

        with patch.object(
            graph._graph,
            "stream",
            return_value=iter([(tool_msg, {}), (ai_chunk, {})]),
        ):
            result = list(graph.stream([], "hi", 0))

        self.assertEqual(result, ["Hello"])
