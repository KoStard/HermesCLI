from .openai import OpenAIModel

class OpenRouterModel(OpenAIModel):
    def initialize(self):
        self.config = dict(self.config)
        self.config["OPENAI"] = {
            "api_key": self.config["OPENROUTER"]["api_key"],
            "base_url": "https://openrouter.ai/api/v1",
            "model": self.config["OPENROUTER"].get("model", "openai/gpt-3.5-turbo"),
        }
        super().initialize()
