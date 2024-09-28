from .openai import OpenAIModel
from ..registry import register_model

@register_model(name=["openrouter", "openrouter/perplexity", "openrouter/o1-mini"], file_processor="default", prompt_builder="openai", config_key='OPENROUTER')
class OpenRouterModel(OpenAIModel):
    def initialize(self):
        model_identifier = self.config["model_identifier"]
        model_id = self.get_model_id(model_identifier)
        self.config = {
            "api_key": self.config.get("api_key"),
            "base_url": "https://openrouter.ai/api/v1",
            "model": model_id
        }
        super().initialize()

    def get_model_id(self, model_identifier):
        if model_identifier == 'openrouter/perplexity':
            return 'perplexity/llama-3.1-sonar-large-128k-online'
        elif model_identifier == 'openrouter/o1-mini':
            return 'openai/o1-mini-2024-09-12'
        elif model_identifier == 'openrouter':
            return self.config.get("model", "openai/o1-mini-2024-09-12")