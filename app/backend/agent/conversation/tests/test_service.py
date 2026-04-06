from unittest.mock import MagicMock, patch

from django.test import TestCase

from conversation.service import OpenAIClient


class OpenAIClientStreamTest(TestCase):

    @patch('conversation.service.OpenAI')
    def test_stream_passes_messages_list_to_openai(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.responses.create.return_value = []

        client = OpenAIClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "hello"},
        ]
        list(client.stream(messages))

        mock_client.responses.create.assert_called_once_with(
            model="gpt-4o-mini",
            stream=True,
            input=messages,
        )

    @patch('conversation.service.OpenAI')
    def test_stream_yields_text_delta_only(self, mock_openai_cls):
        from openai.types.responses import ResponseTextDeltaEvent

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        delta_event = MagicMock()
        delta_event.__class__ = ResponseTextDeltaEvent
        delta_event.delta = "hello"
        non_delta_event = MagicMock()
        mock_client.responses.create.return_value = [delta_event, non_delta_event]

        client = OpenAIClient()
        result = list(client.stream([{"role": "user", "content": "hi"}]))

        self.assertEqual(result, ["hello"])
