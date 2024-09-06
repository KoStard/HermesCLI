from typing import Generator
from .openai import OpenAIModel

class OpenRouterModel(OpenAIModel):
    def initialize(self):
        self.config = dict(self.config)
        self.config["OPENAI"] = {
            "api_key": self.config["OPENROUTER"]["api_key"],
            "base_url": "https://openrouter.ai/api/v1",
            "model": self.config["OPENROUTER"].get("model", "openai/gpt-3.5-turbo"),
        }
        self.site_url = self.config["OPENROUTER"].get("site_url", "")
        self.app_name = self.config["OPENROUTER"].get("app_name", "")
        super().initialize()

    def send_message(self, message: str) -> Generator[str, None, None]:
        return super().send_message(message)
