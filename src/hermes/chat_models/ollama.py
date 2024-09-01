from typing import Generator
from .base import ChatModel
import ollama

class OllamaModel(ChatModel):
    def initialize(self):
        self.model = self.config["OLLAMA"]["model"]
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        

        response = ollama.chat(
            model=self.model,
            messages=self.messages.copy(),
            stream=True,
        )
        full_response = ""
        for chunk in response:
            content = chunk['message']['content']
            full_response += content
            yield content

        self.messages.append({"role": "assistant", "content": full_response})
