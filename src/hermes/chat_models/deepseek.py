from .openai import OpenAIModel
from ..decorators import register_model

@register_model("deepseek", "default", "xml")
class DeepSeekModel(OpenAIModel):
    def initialize(self):
        self.config = dict(self.config)
        self.config["OPENAI"] = {
            "api_key": self.config["DEEPSEEK"]["api_key"],
            "base_url": self.config["DEEPSEEK"].get("base_url", "https://api.deepseek.com"),
            "model": self.config["DEEPSEEK"].get("model", "deepseek-coder")
        }
        super().initialize()
