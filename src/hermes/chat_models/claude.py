from typing import Generator
from .base import ChatModel
import anthropic
from ..decorators import register_model

@register_model("claude")
class ClaudeModel(ChatModel):
    def initialize(self):
        api_key = self.config["ANTHROPIC"]["api_key"]
        self.client = anthropic.Anthropic(api_key=api_key)
        self.messages = []

    def send_message(self, message) -> Generator[str, None, None]:
        temp_messages = self.messages.copy()
        temp_messages.append({"role": "user", "content": message})
        with self.client.messages.stream(
            model="claude-3-5-sonnet-20240620",
            messages=temp_messages,
            max_tokens=1024
        ) as stream:
            full_response = ""
            for text in stream.text_stream:
                full_response += text
                yield text
        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "assistant", "content": full_response})
