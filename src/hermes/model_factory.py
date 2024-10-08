import os
import configparser
import logging
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
from .chat_models.vertex import VertexModel
from .file_processors.bedrock import BedrockFileProcessor
from .file_processors.default import DefaultFileProcessor
from .prompt_builders.xml_prompt_builder import XMLPromptBuilder
from .prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder
from .prompt_builders.claude_prompt_builder import ClaudePromptBuilder
from .prompt_builders.markdown_prompt_builder import MarkdownPromptBuilder
from .prompt_builders.openai_prompt_builder import OpenAIPromptBuilder

from .registry import ModelRegistry

logger = logging.getLogger(__name__)

def get_default_model(config):
    if 'BASE' in config and 'model' in config['BASE']:
        return config['BASE']['model']
    return None

def merge_configs(base_config: dict, model_config: dict) -> dict:
    merged = base_config.copy()
    merged.update(model_config)
    if 'model' in merged:
        del merged['model']
    return merged

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

    try:
        config_key = ModelRegistry.get_config_key(model_name)
    except Exception as e:
        logger.debug(f"Error getting config key for model {model_name}: {str(e)}")
        logger.error(f"Model {model_name} not found, available models: {ModelRegistry.get_available_models()}")
        raise e

    base_config = dict(config['BASE']) if 'BASE' in config else {}
    model_config = dict(config[config_key]) if config_key in config else {}
    merged_config = merge_configs(base_config, model_config)

    model, file_processor, prompt_builder_class = ModelRegistry.create_model(model_name, merged_config)

    return model, file_processor, prompt_builder_class
