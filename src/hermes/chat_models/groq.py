from typing import Generator
from .base import ChatModel
from groq import Groq
from ..decorators import register_model

@register_model("groq", "default", "markdown")
class GroqModel(ChatModel):
    def initialize(self):
        api_key = self.config["GROQ"]["api_key"]
        self.model = self.config["GROQ"].get("model", "llama3-8b-8192")
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
