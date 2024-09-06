from typing import Generator
from .openai import OpenAIModel

class DeepSeekModel(OpenAIModel):
    def initialize(self):
        self.config["OPENAI"] = {
            "api_key": self.config["DEEPSEEK"]["api_key"],
            "base_url": self.config["DEEPSEEK"].get("base_url", "https://api.deepseek.com"),
            "model": self.config["DEEPSEEK"].get("model", "deepseek-coder")
        }
        super().initialize()

    def send_message(self, message: str) -> Generator[str, None, None]:
        return super().send_message(message)
