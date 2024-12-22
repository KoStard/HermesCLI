from .openai import OpenAIModel

class XAIModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": self.config.get("base_url", "https://api.x.ai/v1"),
            "model": self.config.get("model", "grok-beta")
        }
        super().initialize()

    @staticmethod
    def get_provider() -> str:
        return 'XAI'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        return ["grok-beta", "grok-2-1212"]
