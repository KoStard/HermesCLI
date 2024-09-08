"""
Proposal: Configuration-Based Model Creation

This proposal suggests using a configuration file to define models and their associated components.

Pros:
1. Highly flexible and extensible
2. Easy to add new models without code changes
3. Clear separation of configuration and implementation
4. Allows for easy customization of existing models

Cons:
1. Requires careful management of the configuration file
2. Might be overkill for projects with a small number of models
3. Could introduce runtime errors if configuration is invalid

Example implementation:
"""

import yaml
import importlib
from typing import Dict, Any

class ModelManager:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def create_model(self, model_name: str) -> Any:
        if model_name not in self.config['models']:
            raise ValueError(f"Unknown model: {model_name}")

        model_config = self.config['models'][model_name]
        model_class = self._import_class(model_config['class'])
        file_processor_class = self._import_class(model_config['file_processor'])
        prompt_builder_class = self._import_class(model_config['prompt_builder'])

        file_processor = file_processor_class()
        prompt_builder = prompt_builder_class(file_processor)
        return model_class(prompt_builder, **model_config.get('params', {}))

    def _import_class(self, class_path: str) -> type:
        module_name, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

# Example configuration file (config.yaml):
"""
models:
  bedrock:
    class: hermes.chat_models.bedrock.BedrockModel
    file_processor: hermes.file_processors.default.DefaultFileProcessor
    prompt_builder: hermes.prompt_builders.bedrock_prompt_builder.BedrockPromptBuilder
    params:
      model_tag: claude
  openai:
    class: hermes.chat_models.openai.OpenAIModel
    file_processor: hermes.file_processors.default.DefaultFileProcessor
    prompt_builder: hermes.prompt_builders.openai_prompt_builder.OpenAIPromptBuilder
    params:
      api_key: your_api_key_here
"""

# Usage
manager = ModelManager('config.yaml')
bedrock_model = manager.create_model('bedrock')
openai_model = manager.create_model('openai')
