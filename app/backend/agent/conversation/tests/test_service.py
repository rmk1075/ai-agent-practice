from unittest.mock import MagicMock, patch

from django.test import TestCase
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from conversation.models import Message
from conversation.service import ConversationGraph


class ConversationGraphStreamTest(TestCase):

    @patch('conversation.service.ChatOpenAI')
    def test_stream_yields_text_tokens(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        chunk1 = MagicMock()
        chunk1.content = "Hello"
        chunk2 = MagicMock()
        chunk2.content = " world"
        empty_chunk = MagicMock()
        empty_chunk.content = ""

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are a helpful assistant.",
        )

        with patch.object(graph._graph, 'stream', return_value=iter([
            (chunk1, {}), (empty_chunk, {}), (chunk2, {})
        ])):
            result = list(graph.stream([], "hi"))

        self.assertEqual(result, ["Hello", " world"])

    @patch('conversation.service.ChatOpenAI')
    def test_stream_skips_empty_chunks(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are a helpful assistant.",
        )

        empty = MagicMock()
        empty.content = ""

        with patch.object(graph._graph, 'stream', return_value=iter([(empty, {})])):
            result = list(graph.stream([], "hi"))

        self.assertEqual(result, [])

    @patch('conversation.service.ChatOpenAI')
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

        def fake_stream(input_dict, stream_mode):
            captured['messages'] = input_dict['messages']
            return iter([])

        with patch.object(graph._graph, 'stream', side_effect=fake_stream):
            list(graph.stream([user_msg, assistant_msg], "follow-up"))

        msgs = captured['messages']
        self.assertEqual(len(msgs), 3)
        self.assertIsInstance(msgs[0], HumanMessage)
        self.assertEqual(msgs[0].content, "first message")
        self.assertIsInstance(msgs[1], AIMessage)
        self.assertEqual(msgs[1].content, "first reply")
        self.assertIsInstance(msgs[2], HumanMessage)
        self.assertEqual(msgs[2].content, "follow-up")

    @patch('conversation.service.ChatOpenAI')
    def test_graph_uses_system_prompt_in_chatbot_node(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content="response")

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are a pirate.",
        )

        state = {"messages": [HumanMessage(content="hello")]}
        result = graph._chatbot_node(state)

        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIsInstance(call_args[0], SystemMessage)
        self.assertEqual(call_args[0].content, "You are a pirate.")
        self.assertEqual(result["messages"][0].content, "response")
