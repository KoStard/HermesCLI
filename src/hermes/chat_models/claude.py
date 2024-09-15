from typing import Generator
from .base import ChatModel
import anthropic
from ..decorators import register_model

@register_model("claude", "default", "claude")
class ClaudeModel(ChatModel):
    def initialize(self):
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Claude model")
        self.client = anthropic.Anthropic(api_key=api_key)

    def send_history(self, messages) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model="claude-3-5-sonnet-20240620",
            messages=messages,
            max_tokens=1024
        ) as stream:
            for text in stream.text_stream:
                yield text
