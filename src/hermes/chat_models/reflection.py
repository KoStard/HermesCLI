from .openai import OpenAIModel
from ..decorators import register_model

@register_model("reflection", "default", "markdown")
class ReflectionModel(OpenAIModel):
    def initialize(self):
        self.config = dict(self.config)
        self.config["OPENAI"] = {
            "api_key": self.config["REFLECTION"]["api_key"],
            "base_url": "https://openrouter.ai/api/v1",
            "model": self.config["REFLECTION"].get("model", "mattshumer/reflection-70b"),
        }
        super().initialize()
