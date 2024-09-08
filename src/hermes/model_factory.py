import os
import configparser
from typing import Tuple

from hermes.prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder
from hermes.prompt_builders.markdown_prompt_builder import MarkdownPromptBuilder
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder
from hermes.prompt_builders.claude_prompt_builder import ClaudePromptBuilder
from hermes.prompt_builders.openai_prompt_builder import OpenAIPromptBuilder
from hermes.file_processors.default import DefaultFileProcessor
from hermes.chat_models.claude import ClaudeModel
from hermes.chat_models.bedrock import BedrockModel
from hermes.chat_models.gemini import GeminiModel
from hermes.chat_models.openai import OpenAIModel
from hermes.chat_models.ollama import OllamaModel
from hermes.chat_models.deepseek import DeepSeekModel
from hermes.chat_models.reflection import ReflectionModel
from hermes.chat_models.groq import GroqModel
from hermes.chat_models.base import ChatModel
from hermes.prompt_builders.base import PromptBuilder

def get_default_model(config):
    if 'BASE' in config and 'model' in config['BASE']:
        return config['BASE']['model']
    return None

def create_model_and_processors(model_name: str | None) -> Tuple[ChatModel, PromptBuilder]:
    config = configparser.ConfigParser()
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "multillmchat")
    config_path = os.path.join(config_dir, "config.ini")
    os.makedirs(config_dir, exist_ok=True)
    config.read(config_path)

    if model_name is None:
        model_name = get_default_model(config)
        if model_name is None:
            raise Exception("No model specified and no default model found in config. Use --model to specify a model or set a default in the config file.")

    if model_name == "claude":
        model = ClaudeModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = ClaudePromptBuilder(file_processor)
    elif model_name.startswith("bedrock-"):
        model_tag = '-'.join(model_name.split("-")[1:])
        model = BedrockModel(config, model_tag)
        file_processor = DefaultFileProcessor()
        prompt_builder = BedrockPromptBuilder(file_processor)
    elif model_name == "gemini":
        model = GeminiModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name == "openai":
        model = OpenAIModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = OpenAIPromptBuilder(file_processor)
    elif model_name == "ollama":
        model = OllamaModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name == "deepseek":
        model = DeepSeekModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = XMLPromptBuilder(file_processor)
    elif model_name == "reflection":
        model = ReflectionModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = MarkdownPromptBuilder(file_processor)
    elif model_name == "groq":
        model = GroqModel(config)
        file_processor = DefaultFileProcessor()
        prompt_builder = MarkdownPromptBuilder(file_processor)
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    return model, prompt_builder
