from typing import Generator
from .base import ChatModel
import ollama
from ..decorators import register_model

@register_model("ollama", "default", "xml")
class OllamaModel(ChatModel):
    def initialize(self):
        self.model = self.config["OLLAMA"]["model"]

    def send_history(self, messages) -> Generator[str, None, None]:
        response = ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in response:
            yield chunk['message']['content']
