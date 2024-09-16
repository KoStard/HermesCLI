import os
import configparser
from typing import Tuple

from hermes.chat_models.base import ChatModel
from hermes.prompt_builders.base import PromptBuilder

# Import all the models, file processors and prompt builders, one by one, to register them
from .chat_models.bedrock import BedrockModel
from .chat_models.claude import ClaudeModel
from .chat_models.gemini import GeminiModel
from .chat_models.openai import OpenAIModel
from .chat_models.ollama import OllamaModel
from .chat_models.groq import GroqModel
from .chat_models.sambanova import SambanovaModel
from .chat_models.deepseek import DeepSeekModel
from .chat_models.open_router import OpenRouterModel
from .file_processors.bedrock import BedrockFileProcessor
from .file_processors.default import DefaultFileProcessor
from .prompt_builders.xml_prompt_builder import XMLPromptBuilder
from .prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder
from .prompt_builders.claude_prompt_builder import ClaudePromptBuilder
from .prompt_builders.markdown_prompt_builder import MarkdownPromptBuilder
from .prompt_builders.openai_prompt_builder import OpenAIPromptBuilder

from .registry import ModelRegistry

def get_default_model(config):
    if 'BASE' in config and 'model' in config['BASE']:
        return config['BASE']['model']
    return None

def create_model_and_processors(model_name: str | None) -> Tuple[ChatModel, str, PromptBuilder]:
    config = configparser.ConfigParser()
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "hermes")
    config_path = os.path.join(config_dir, "config.ini")
    os.makedirs(config_dir, exist_ok=True)
    config.read(config_path)

    if model_name is None:
        model_name = get_default_model(config)
        if model_name is None:
            raise Exception("No model specified and no default model found in config. Use --model to specify a model or set a default in the config file.")

    config_key = ModelRegistry.get_config_key(model_name)
    model_config = dict(config[config_key]) if config_key in config else {}
    model, file_processor, prompt_builder_class = ModelRegistry.create_model(model_name, model_config)

    return model, model_name, file_processor, prompt_builder_class
