from typing import Generator
from .base import ChatModel
import ollama

class OllamaModel(ChatModel):
    def initialize(self):
        self.model = self.config["OLLAMA"]["model"]
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        
        stream = ollama.chat(
            model=self.model,
            messages=list(self.messages),
            stream=True,
        )

        full_response = ""
        for chunk in stream:
            content = chunk['message']['content']
            full_response += content
            yield content

        self.messages.append({"role": "assistant", "content": full_response})
