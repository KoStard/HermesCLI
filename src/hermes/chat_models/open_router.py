from .openai import OpenAIModel
from ..decorators import register_model

@register_model("openrouter", "default", "markdown")
class OpenRouterModel(OpenAIModel):
    def initialize(self):
        self.config = dict(self.config)
        self.config["OPENAI"] = {
            "api_key": self.config["OPENROUTER"]["api_key"],
            "base_url": "https://openrouter.ai/api/v1",
            "model": self.config["OPENROUTER"].get("model", "openai/o1-mini-2024-09-12")
        }
        super().initialize()
