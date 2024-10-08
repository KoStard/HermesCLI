from typing import Generator
from .base import ChatModel
from ..registry import register_model

@register_model(name="ollama", file_processor="default", prompt_builder="xml", config_key='OLLAMA')
class OllamaModel(ChatModel):
    def initialize(self):
        import ollama
        self.chat = ollama.chat
        self.model = self.config.get("model", "llama2")

    def send_history(self, messages) -> Generator[str, None, None]:
        response = self.chat(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in response:
            yield chunk['message']['content']
