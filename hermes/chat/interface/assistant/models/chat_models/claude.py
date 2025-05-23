from collections.abc import Generator
from typing import Any

from hermes.chat.interface.assistant.models.prompt_builder.simple_prompt_builder import (
    SimplePromptBuilderFactory,
)
from hermes.chat.interface.assistant.models.request_builder.base import RequestBuilder
from hermes.chat.interface.assistant.models.request_builder.claude import ClaudeRequestBuilder

from .base import ChatModel


class ClaudeModel(ChatModel):
    def initialize(self):
        import anthropic

        self.request_builder = ClaudeRequestBuilder(self.model_tag, self.notifications_printer, SimplePromptBuilderFactory())

        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Claude model")
        self.client = anthropic.Anthropic(api_key=api_key, default_headers={"anthropic-beta": "pdfs-2024-09-25"})

    def send_request(self, request: Any) -> Generator[str, None, None]:
        with self.client.messages.stream(**request) as stream:
            yield from stream.text_stream

    def get_request_builder(self) -> RequestBuilder:
        return self.request_builder

    @staticmethod
    def get_provider() -> str:
        return "ANTHROPIC"

    @staticmethod
    def get_model_tags() -> list[str]:
        return [
            "claude-3-5-sonnet-20240620",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]
