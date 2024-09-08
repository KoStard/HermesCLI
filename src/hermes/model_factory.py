import os
import configparser
from typing import Tuple

from .registry import ModelRegistry
from .chat_models.base import ChatModel
from .prompt_builders.base import PromptBuilder
from .file_processors.base import FileProcessor

def get_default_model(config):
    if 'BASE' in config and 'model' in config['BASE']:
        return config['BASE']['model']
    return None

def create_model_and_processors(model_name: str | None) -> Tuple[ChatModel, str, PromptBuilder]:
    config = configparser.ConfigParser()
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "multillmchat")
    config_path = os.path.join(config_dir, "config.ini")
    os.makedirs(config_dir, exist_ok=True)
    config.read(config_path)

    if model_name is None:
        model_name = get_default_model(config)
        if model_name is None:
            raise Exception("No model specified and no default model found in config. Use --model to specify a model or set a default in the config file.")

    model_class = ModelRegistry.get_model(model_name)
    file_processor_class = ModelRegistry.get_file_processor("default")
    prompt_builder_class = ModelRegistry.get_prompt_builder(model_name)

    file_processor = file_processor_class()
    prompt_builder = prompt_builder_class(file_processor)
    
    if model_name.startswith("bedrock-"):
        model_tag = '-'.join(model_name.split("-")[1:])
        model = model_class(config, model_tag)
    else:
        model = model_class(config)

    return model, model_name, prompt_builder
