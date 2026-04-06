from typing import Any, Generator

from openai import OpenAI
from openai.types.responses import ResponseTextDeltaEvent


class OpenAIClient:
    def __init__(self):
        self._client = OpenAI()

    def stream(self, messages: list[dict]) -> Generator[str, Any, Any]:
        for response in self._client.responses.create(
            model="gpt-4o-mini",
            stream=True,
            input=messages,
        ):
            if isinstance(response, ResponseTextDeltaEvent):
                yield response.delta
