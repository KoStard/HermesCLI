"""
Proposal: Decorator-Based Model Registration

This proposal suggests using decorators to register models and their components.

Pros:
1. Intuitive and Pythonic way of registering models
2. Keeps model definitions and registrations close together
3. Easy to add new models by simply defining a new class with decorators
4. Allows for fine-grained control over model configuration

Cons:
1. Might scatter model definitions across multiple files
2. Could lead to circular import issues if not carefully managed
3. Requires understanding of Python decorators

Example implementation:
"""

from typing import Dict, Type, Callable
import functools

class ModelRegistry:
    models: Dict[str, Type] = {}
    file_processors: Dict[str, Type] = {}
    prompt_builders: Dict[str, Type] = {}

    @classmethod
    def register_model(cls, name: str):
        def decorator(model_class: Type):
            cls.models[name] = model_class
            return model_class
        return decorator

    @classmethod
    def register_file_processor(cls, name: str):
        def decorator(processor_class: Type):
            cls.file_processors[name] = processor_class
            return processor_class
        return decorator

    @classmethod
    def register_prompt_builder(cls, name: str):
        def decorator(builder_class: Type):
            cls.prompt_builders[name] = builder_class
            return builder_class
        return decorator

    @classmethod
    def create_model(cls, name: str, config: dict):
        if name not in cls.models:
            raise ValueError(f"Unknown model: {name}")
        model_class = cls.models[name]
        file_processor = cls.file_processors.get(config.get('file_processor', 'default'))()
        prompt_builder = cls.prompt_builders[config['prompt_builder']](file_processor)
        return model_class(prompt_builder, **config.get('params', {}))

# Usage in model definition files:

@ModelRegistry.register_model("bedrock")
class BedrockModel:
    def __init__(self, prompt_builder, model_tag: str):
        self.prompt_builder = prompt_builder
        self.model_tag = model_tag

@ModelRegistry.register_file_processor("default")
class DefaultFileProcessor:
    def process(self, file_path: str):
        # Implementation here
        pass

@ModelRegistry.register_prompt_builder("bedrock")
class BedrockPromptBuilder:
    def __init__(self, file_processor):
        self.file_processor = file_processor

    def build(self, prompt: str):
        # Implementation here
        pass

# Usage in main application:
config = {
    'bedrock': {
        'prompt_builder': 'bedrock',
        'file_processor': 'default',
        'params': {
            'model_tag': 'claude'
        }
    }
}

model = ModelRegistry.create_model('bedrock', config['bedrock'])
