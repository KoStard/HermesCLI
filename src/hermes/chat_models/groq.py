from typing import Generator
from .base import ChatModel
from groq import Groq
from ..decorators import register_model

@register_model(name="groq", file_processor="default", prompt_builder="markdown", config_key='GROQ')
class GroqModel(ChatModel):
    def initialize(self):
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for Groq model")
        self.model = self.config.get("model", "llama3-8b-8192")
        self.client = Groq(api_key=api_key)

    def send_history(self, messages) -> Generator[str, None, None]:
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                stream=True
            )
        except Exception as e:
            raise Exception(f"Error communicating with Groq API:", e)

        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
