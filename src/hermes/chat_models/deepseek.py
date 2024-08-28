from typing import Generator
from .base import ChatModel
from openai import OpenAI

class DeepSeekModel(ChatModel):
    def initialize(self):
        api_key = self.config["DEEPSEEK"]["api_key"]
        base_url = self.config["DEEPSEEK"].get("base_url", "https://api.deepseek.com")
        model = self.config["DEEPSEEK"].get("model", "deepseek-coder")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True
        )
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content
        self.messages.append({"role": "assistant", "content": full_response})
