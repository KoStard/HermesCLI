from typing import Generator
from .base import ChatModel
import anthropic

class ClaudeModel(ChatModel):
    def initialize(self):
        api_key = self.config["ANTHROPIC"]["api_key"]
        self.client = anthropic.Anthropic(api_key=api_key)
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        with self.client.messages.stream(
            model="claude-3-5-sonnet-20240620",
            messages=self.messages,
            max_tokens=1024
        ) as stream:
            for text in stream.text_stream:
                yield text
        self.messages.append({"role": "assistant", "content": message})
