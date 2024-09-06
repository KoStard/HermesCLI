from typing import Generator
from .base import ChatModel
from groq import Groq

class GroqModel(ChatModel):
    def initialize(self):
        api_key = self.config["GROQ"]["api_key"]
        self.model = self.config["GROQ"].get("model", "llama3-8b-8192")
        self.client = Groq(api_key=api_key)
        self.messages = [
            {"role": "system", "content": "You are a world-class AI system, capable of complex reasoning and reflection. Reason through the query inside <thinking> tags, and then provide your final response inside <output> tags. If you detect that you made a mistake in your reasoning at any point, correct yourself inside <reflection> tags."}
        ]

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        try:
            response = self.client.chat.completions.create(
                messages=self.messages,
                model=self.model,
                stream=True
            )
        except Exception as e:
            raise Exception(f"Error communicating with Groq API: {str(e)}")

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content
        self.messages.append({"role": "assistant", "content": full_response})
