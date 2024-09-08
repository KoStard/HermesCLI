from typing import Dict, Type, Tuple
from .chat_models.base import ChatModel
from .file_processors.base import FileProcessor
from .prompt_builders.base import PromptBuilder

class ModelRegistry:
    models: Dict[str, Tuple[Type[ChatModel], str, str]] = {}
    file_processors: Dict[str, Type[FileProcessor]] = {}
    prompt_builders: Dict[str, Type[PromptBuilder]] = {}

    @classmethod
    def register_model(cls, name: str, file_processor: str, prompt_builder: str):
        def decorator(model_class: Type[ChatModel]):
            cls.models[name] = (model_class, file_processor, prompt_builder)
            return model_class
        return decorator

    @classmethod
    def register_file_processor(cls, name: str):
        def decorator(processor_class: Type[FileProcessor]):
            cls.file_processors[name] = processor_class
            return processor_class
        return decorator

    @classmethod
    def register_prompt_builder(cls, name: str):
        def decorator(builder_class: Type[PromptBuilder]):
            cls.prompt_builders[name] = builder_class
            return builder_class
        return decorator

    @classmethod
    def get_model(cls, name: str) -> Tuple[Type[ChatModel], str, str]:
        return cls.models[name]

    @classmethod
    def get_file_processor(cls, name: str) -> Type[FileProcessor]:
        return cls.file_processors[name]

    @classmethod
    def get_prompt_builder(cls, name: str) -> Type[PromptBuilder]:
        return cls.prompt_builders[name]

    @classmethod
    def create_model(cls, name: str, config: dict) -> ChatModel:
        model_class, file_processor_name, prompt_builder_name = cls.get_model(name)
        file_processor = cls.get_file_processor(file_processor_name)()
        prompt_builder = cls.get_prompt_builder(prompt_builder_name)(file_processor)
        return model_class(config, prompt_builder)
