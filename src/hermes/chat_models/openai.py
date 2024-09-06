from typing import Generator
from .base import ChatModel
import openai

class OpenAIModel(ChatModel):
    def initialize(self):
        api_key = self.config["OPENAI"]["api_key"]
        base_url = self.config["OPENAI"].get("base_url", "https://api.openai.com/v1")
        model = self.config["OPENAI"].get("model", "gpt-4-0125-preview")
        self.client = openai.Client(api_key=api_key, base_url=base_url)
        self.model = model
        self.messages = []
        
    def add_system_message(self, message: str):
        self.messages.append({"role": "system", "content": message})

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=True
            )
        except openai.AuthenticationError:
            raise Exception("Authentication failed. Please check your API key.")
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content
        self.messages.append({"role": "assistant", "content": full_response})
