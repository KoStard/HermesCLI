from .openai import OpenAIModel

class DeepSeekModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": self.config.get("base_url", "https://api.deepseek.com"),
            "model": self.config.get("model", "deepseek-chat")
        }
        super().initialize()

    @staticmethod
    def get_provider() -> str:
        return 'DEEPSEEK'
    
    @staticmethod
    def get_model_tags() -> list[str]:
        return ["deepseek-chat"]
