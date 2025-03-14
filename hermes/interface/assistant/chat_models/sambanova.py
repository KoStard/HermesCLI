from .openai import OpenAIModel


class SambanovaModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": "https://api.sambanova.ai/v1",
            "model": self.config.get("model", "Meta-Llama-3.1-405B-Instruct"),
        }
        super().initialize()

    @staticmethod
    def get_provider() -> str:
        return "SAMBANOVA"

    @staticmethod
    def get_model_tags() -> list[str]:
        return ["Meta-Llama-3.1-405B-Instruct"]
