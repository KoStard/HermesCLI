from .openai import OpenAIModel
from ..decorators import register_model

@register_model("reflection", "default", "markdown")
class ReflectionModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": "https://openrouter.ai/api/v1",
            "model": self.config.get("model", "mattshumer/reflection-70b"),
        }
        super().initialize()
