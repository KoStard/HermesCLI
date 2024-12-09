from typing import Generator
from .openai import OpenAIModel

class GroqModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": self.config.get("base_url", "https://api.groq.com/openai/v1")
        }
        super().initialize()

    @staticmethod
    def get_provider() -> str:
        return 'GROQ'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        return ["llama3-8b-8192"]
