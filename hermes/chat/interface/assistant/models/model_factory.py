from configparser import ConfigParser
from typing import Any

from hermes.chat.interface.assistant.models.chat_models.base import ChatModel
from hermes.chat.interface.assistant.models.chat_models.bedrock import BedrockModel
from hermes.chat.interface.assistant.models.chat_models.claude import ClaudeModel
from hermes.chat.interface.assistant.models.chat_models.deepseek import DeepSeekModel
from hermes.chat.interface.assistant.models.chat_models.gemini2 import Gemini2Model
from hermes.chat.interface.assistant.models.chat_models.groq import GroqModel
from hermes.chat.interface.assistant.models.chat_models.open_router import OpenRouterModel
from hermes.chat.interface.assistant.models.chat_models.openai import OpenAIModel
from hermes.chat.interface.assistant.models.chat_models.sambanova import SambanovaModel
from hermes.chat.interface.assistant.models.chat_models.xai import XAIModel
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.utils.config_utils import extract_config_section


class ModelFactory:
    def __init__(self, notifications_printer: CLINotificationsPrinter):
        self.notifications_printer = notifications_printer
        self.model_classes: list[type[ChatModel]] = [
            OpenAIModel,
            ClaudeModel,
            Gemini2Model,
            GroqModel,
            DeepSeekModel,
            SambanovaModel,
            OpenRouterModel,
            BedrockModel,
            XAIModel,
        ]

        # Create mapping of (provider, model_tag) -> model_class
        self.provider_model_map = {}
        for model_class in self.model_classes:
            provider = model_class.get_provider().upper()
            for model_tag in model_class.get_model_tags():
                self.provider_model_map[(provider, model_tag)] = model_class

        # Create list of all known provider+model_tag pairs
        self.provider_and_model_tag_pairs = list(self.provider_model_map.keys())

    def get_provider_model_pairs(self) -> list[tuple]:
        """Returns a list of all known (provider, model_tag) pairs

        Returns:
            List[tuple]: List of (provider, model_tag) tuples
        """
        return self.provider_and_model_tag_pairs

    def get_model(self, provider: str, model_tag: str, config: ConfigParser | dict[str, Any]) -> ChatModel:
        """Creates and returns an appropriate chat model instance based on the provider and model tag.

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

        # First try exact match
        model_class = self.provider_model_map.get((provider, model_tag))
        if model_class:
            config_section_name = model_class.get_config_section_name()
            config_section = extract_config_section(config, config_section_name)
            return model_class(config_section, model_tag, self.notifications_printer)

        # If no exact match, find all classes for this provider
        matching_classes = [m for m in self.model_classes if m.get_provider().upper() == provider]

        if not matching_classes:
            supported_providers = list(set(m.get_provider().upper() for m in self.model_classes))
            raise ValueError(f"Unsupported model provider: {provider}, supported providers: {supported_providers}")

        if len(matching_classes) > 1:
            self.notifications_printer.print_notification(
                f"Multiple model implementations found for provider '{provider}' "
                f"and unknown model tag '{model_tag}'. Using first implementation: "
                f"{matching_classes[0].__name__}",
            )

        model_class = matching_classes[0]
        config_section_name = model_class.get_config_section_name()
        config_section = extract_config_section(config, config_section_name)
        # Use first matching class
        return model_class(config_section, model_tag, self.notifications_printer)
