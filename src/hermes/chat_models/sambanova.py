from .openai import OpenAIModel
from ..decorators import register_model

@register_model("sambanova", "default", "markdown")
class SambanovaModel(OpenAIModel):
    def initialize(self):
        self.config = dict(self.config)
        self.config["OPENAI"] = {
            "api_key": self.config["SAMBANOVA"]["api_key"],
            "base_url": "https://api.sambanova.ai/v1",
            "model": self.config["SAMBANOVA"].get("model", "Meta-Llama-3.1-405B-Instruct")
        }
        super().initialize()
