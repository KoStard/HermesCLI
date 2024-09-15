from typing import Generator
from .base import ChatModel
import openai
from ..decorators import register_model

@register_model("openai", "default", "openai")
class OpenAIModel(ChatModel):
    def initialize(self):
        api_key = self.config["OPENAI"]["api_key"]
        base_url = self.config["OPENAI"].get("base_url", "https://api.openai.com/v1")
        model = self.config["OPENAI"].get("model", "gpt-4o")
        self.client = openai.Client(api_key=api_key, base_url=base_url)
        self.model = model

    def send_history(self, messages) -> Generator[str, None, None]:
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
        except openai.AuthenticationError:
            raise Exception("Authentication failed. Please check your API key.")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
