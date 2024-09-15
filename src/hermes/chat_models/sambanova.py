from .openai import OpenAIModel
from ..decorators import register_model

@register_model(name="sambanova", file_processor="default", prompt_builder="markdown", config_key='SAMBANOVA')
class SambanovaModel(OpenAIModel):
    def initialize(self):
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": "https://api.sambanova.ai/v1",
            "model": self.config.get("model", "Meta-Llama-3.1-405B-Instruct")
        }
        super().initialize()
