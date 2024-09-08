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
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        temp_messages = self.messages.copy()
        temp_messages.append({"role": "user", "content": message})
        try:
            response = self.client.chat.completions.create(
                messages=temp_messages,
                model=self.model,
                stream=True
            )
        except Exception as e:
            raise Exception(f"Error communicating with Groq API:", e)

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content
        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "assistant", "content": full_response})
