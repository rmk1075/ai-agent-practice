from unittest.mock import MagicMock, patch

from django.test import TestCase
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from conversation.models import Conversation, ConversationMetadata, Message
from conversation.service import ConversationGraph


class ConversationGraphMetadataNodeTest(TestCase):

    @patch('conversation.service.ChatOpenAI')
    def test_metadata_node_formats_metadata_as_context(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()
        conv = Conversation.objects.create(name='test')
        ConversationMetadata.objects.create(conversation=conv, key='user_name', value='John')
        ConversationMetadata.objects.create(conversation=conv, key='role', value='Lawyer')

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
            conversation_id=conv.id,
        )
        result = graph._metadata_node({})

        self.assertEqual(result['metadata_context'], "\n\nContext:\n- user_name: John\n- role: Lawyer")

    @patch('conversation.service.ChatOpenAI')
    def test_metadata_node_returns_empty_string_when_no_metadata(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()
        conv = Conversation.objects.create(name='test')

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
            conversation_id=conv.id,
        )
        result = graph._metadata_node({})

        self.assertEqual(result['metadata_context'], "")

    @patch('conversation.service.ChatOpenAI')
    def test_metadata_node_excludes_deleted_metadata(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()
        conv = Conversation.objects.create(name='test')
        ConversationMetadata.objects.create(conversation=conv, key='active_key', value='active_value')
        deleted = ConversationMetadata.objects.create(conversation=conv, key='deleted_key', value='deleted_value')
        deleted.delete()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
            conversation_id=conv.id,
        )
        result = graph._metadata_node({})

        self.assertIn('active_key', result['metadata_context'])
        self.assertIn('active_value', result['metadata_context'])
        self.assertNotIn('deleted_key', result['metadata_context'])


class ConversationGraphChatbotNodeTest(TestCase):

    @patch('conversation.service.ChatOpenAI')
    def test_chatbot_node_appends_metadata_context_to_system_prompt(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content="response")

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are helpful.",
            conversation_id=0,
        )
        state = {
            "messages": [HumanMessage(content="hello")],
            "metadata_context": "\n\nContext:\n- role: Lawyer",
        }
        graph._chatbot_node(state)

        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIsInstance(call_args[0], SystemMessage)
        self.assertEqual(call_args[0].content, "You are helpful.\n\nContext:\n- role: Lawyer")

    @patch('conversation.service.ChatOpenAI')
    def test_chatbot_node_uses_system_prompt_only_when_no_metadata(self, mock_llm_cls):
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        mock_llm.invoke.return_value = MagicMock(content="response")

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="You are a pirate.",
            conversation_id=0,
        )
        state = {
            "messages": [HumanMessage(content="hello")],
            "metadata_context": "",
        }
        graph._chatbot_node(state)

        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIsInstance(call_args[0], SystemMessage)
        self.assertEqual(call_args[0].content, "You are a pirate.")


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
            conversation_id=0,
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
            conversation_id=0,
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
            conversation_id=0,
        )

        user_msg = MagicMock(spec=Message)
        user_msg.role = "user"
        user_msg.content = "first message"

        assistant_msg = MagicMock(spec=Message)
        assistant_msg.role = "assistant"
        assistant_msg.content = "first reply"

        captured = {}

        def fake_stream(input_dict, stream_mode):
            captured['input'] = input_dict
            return iter([])

        with patch.object(graph._graph, 'stream', side_effect=fake_stream):
            list(graph.stream([user_msg, assistant_msg], "follow-up"))

        msgs = captured['input']['messages']
        self.assertEqual(len(msgs), 3)
        self.assertIsInstance(msgs[0], HumanMessage)
        self.assertEqual(msgs[0].content, "first message")
        self.assertIsInstance(msgs[1], AIMessage)
        self.assertEqual(msgs[1].content, "first reply")
        self.assertIsInstance(msgs[2], HumanMessage)
        self.assertEqual(msgs[2].content, "follow-up")

    @patch('conversation.service.ChatOpenAI')
    def test_stream_passes_empty_metadata_context_as_initial_state(self, mock_llm_cls):
        mock_llm_cls.return_value = MagicMock()

        graph = ConversationGraph(
            model="gpt-4o-mini",
            temperature=0.7,
            system_prompt="Be helpful.",
            conversation_id=0,
        )

        captured = {}

        def fake_stream(input_dict, stream_mode):
            captured['input'] = input_dict
            return iter([])

        with patch.object(graph._graph, 'stream', side_effect=fake_stream):
            list(graph.stream([], "hello"))

        self.assertEqual(captured['input']['metadata_context'], "")
