from .openai import OpenAIModel
from ..decorators import register_model

@register_model(name="deepseek", file_processor="default", prompt_builder="xml", config_key='DEEPSEEK')
class DeepSeekModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": self.config.get("base_url", "https://api.deepseek.com"),
            "model": self.config.get("model", "deepseek-coder")
        }
        super().initialize()
