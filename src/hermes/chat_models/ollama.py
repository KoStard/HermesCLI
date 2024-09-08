from typing import Generator
from .base import ChatModel
import ollama
from ..decorators import register_model

@register_model("ollama", "default", "xml")
class OllamaModel(ChatModel):
    def initialize(self):
        self.model = self.config["OLLAMA"]["model"]
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        temp_messages = self.messages.copy()
        temp_messages.append({"role": "user", "content": message})
        
        response = ollama.chat(
            model=self.model,
            messages=temp_messages,
            stream=True,
        )
        full_response = ""
        for chunk in response:
            content = chunk['message']['content']
            full_response += content
            yield content

        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "assistant", "content": full_response})
