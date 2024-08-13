from typing import Generator
from .base import ChatModel
import openai

class OpenAIModel(ChatModel):
    def initialize(self):
        api_key = self.config["OPENAI"]["api_key"]
        self.client = openai.Client(api_key=api_key)
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        stream = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=self.messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
        self.messages.append({"role": "assistant", "content": message})
