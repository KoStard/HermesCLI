from typing import Generator
from .base import ChatModel
from ..registry import register_model

@register_model(name="openai", file_processor="default", prompt_builder="openai", config_key='OPENAI')
class OpenAIModel(ChatModel):
    def initialize(self):
        import openai

        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for OpenAI model")
        base_url = self.config.get("base_url", "https://api.openai.com/v1")
        self.model = self.config.get("model", "gpt-4o")
        self.client = openai.Client(api_key=api_key, base_url=base_url)

    def send_history(self, messages) -> Generator[str, None, None]:
        import openai
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
