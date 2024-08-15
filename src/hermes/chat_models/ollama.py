from typing import Generator
from .base import ChatModel
import requests

class OllamaModel(ChatModel):
    def initialize(self):
        self.base_url = self.config["OLLAMA"]["base_url"]
        self.model = "llama2:3.1"
        self.messages = []

    def send_message(self, message: str) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": message})
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": self.messages,
                "stream": True
            },
            stream=True
        )

        for line in response.iter_lines():
            if line:
                content = line.decode('utf-8').split(':', 1)[1].strip()
                if content:
                    yield content

        self.messages.append({"role": "assistant", "content": message})
