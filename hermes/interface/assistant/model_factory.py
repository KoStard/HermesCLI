from typing import List, Type
from hermes.interface.assistant.chat_models.base import ChatModel
from hermes.interface.assistant.chat_models.openai import OpenAIModel
from hermes.interface.assistant.chat_models.claude import ClaudeModel
from hermes.interface.assistant.chat_models.gemini import GeminiModel
from hermes.interface.assistant.chat_models.groq import GroqModel
from hermes.interface.assistant.chat_models.deepseek import DeepSeekModel
from hermes.interface.assistant.chat_models.sambanova import SambanovaModel
from hermes.interface.assistant.chat_models.open_router import OpenRouterModel
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter


class ModelFactory:
    def __init__(self, notifications_printer: CLINotificationsPrinter):
        self.notifications_printer = notifications_printer
        self.model_classes: List[Type[ChatModel]] = [OpenAIModel, ClaudeModel, GeminiModel, GroqModel, DeepSeekModel, SambanovaModel, OpenRouterModel]
        self.provider_to_model_class_map = {model.get_provider().upper(): model for model in self.model_classes}
        self.provider_and_model_tag_pairs = [(model.get_provider().upper(), model_tag) for model in self.model_classes for model_tag in model.get_model_tags()]

    def get_model(self, provider: str, model_tag: str, config_section: dict) -> ChatModel:
        """
        Creates and returns an appropriate chat model instance based on the provider.
        
        Args:
            provider: The model provider (e.g., 'openai', 'anthropic', etc.)
            model_tag: The specific model identifier
            config_section: Configuration dictionary for the model
            
        Returns:
            ChatModel: An instance of the appropriate chat model class
            
        Raises:
            ValueError: If the provider is not supported
        """
        provider = provider.upper()
        
        if provider not in self.provider_to_model_class_map:
            raise ValueError(f"Unsupported model provider: {provider}, supported providers: {self.provider_to_model_class_map.keys()}")
            
        model_class = self.provider_to_model_class_map[provider]
        return model_class(config_section, model_tag, self.notifications_printer)
