from .openai import OpenAIModel
from ..decorators import register_model

@register_model(name="reflection", file_processor="default", prompt_builder="markdown", config_key='REFLECTION')
class ReflectionModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": "https://openrouter.ai/api/v1",
            "model": self.config.get("model", "mattshumer/reflection-70b"),
        }
        super().initialize()
