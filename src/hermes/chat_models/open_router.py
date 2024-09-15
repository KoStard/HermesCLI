from .openai import OpenAIModel
from ..decorators import register_model

@register_model("openrouter", "default", "markdown")
class OpenRouterModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": "https://openrouter.ai/api/v1",
            "model": self.config.get("model", "openai/o1-mini-2024-09-12")
        }
        super().initialize()
