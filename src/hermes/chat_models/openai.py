from typing import Generator
from .base import ChatModel
import openai
from ..decorators import register_model

@register_model("openai", "default", "openai")
class OpenAIModel(ChatModel):
    def initialize(self):
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for OpenAI model")
        base_url = self.config.get("base_url", "https://api.openai.com/v1")
        self.model = self.config.get("model", "gpt-4")
        self.client = openai.Client(api_key=api_key, base_url=base_url)

    def send_history(self, messages) -> Generator[str, None, None]:
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
        except openai.AuthenticationError as e:
            raise Exception("Authentication failed. Please check your API key.", e)
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
