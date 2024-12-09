from .openai import OpenAIModel

class OpenRouterModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": "https://openrouter.ai/api/v1",
        }
        super().initialize()

    @staticmethod
    def get_provider() -> str:
        return 'OPENROUTER'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        return ["perplexity/llama-3.1-sonar-large-128k-online", "openai/o1-mini-2024-09-12"]
