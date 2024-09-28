from typing import Generator
from .base import ChatModel
import ollama
from ..registry import register_model

@register_model(name="ollama", file_processor="default", prompt_builder="xml", config_key='OLLAMA')
class OllamaModel(ChatModel):
    def initialize(self):
        self.model = self.config.get("model", "llama2")

    def send_history(self, messages) -> Generator[str, None, None]:
        response = ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in response:
            yield chunk['message']['content']
