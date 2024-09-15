from typing import Dict, Type, Tuple
from .chat_models.base import ChatModel
from .file_processors.base import FileProcessor
from .prompt_builders.base import PromptBuilder

class ModelRegistry:
    models: Dict[str, Tuple[Type[ChatModel], str, str, str]] = {}
    file_processors: Dict[str, Type[FileProcessor]] = {}
    prompt_builders: Dict[str, Type[PromptBuilder]] = {}

    @classmethod
    def register_model(cls, name: str | list[str], file_processor: str, prompt_builder: str, config_key: str):
        def decorator(model_class: Type[ChatModel]):
            if isinstance(name, list):
                for n in name:
                    cls.models[n] = (model_class, file_processor, prompt_builder, config_key)
            else:
                cls.models[name] = (model_class, file_processor, prompt_builder, config_key)
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
    def get_model_info(cls, name: str) -> Tuple[Type[ChatModel], str, str, str]:
        return cls.models[name]

    @classmethod
    def get_file_processor(cls, name: str) -> Type[FileProcessor]:
        return cls.file_processors[name]

    @classmethod
    def get_prompt_builder(cls, name: str) -> Type[PromptBuilder]:
        return cls.prompt_builders[name]

    @classmethod
    def get_config_key(cls, name: str) -> str:
        return cls.models[name][3]

    @classmethod
    def create_model(cls, model_name: str, model_config: dict) -> Tuple[ChatModel, FileProcessor, Type[PromptBuilder]]:
        model_class, file_processor_name, prompt_builder_name, config_key = cls.get_model_info(model_name)
        model_config['model_identifier'] = model_name
        file_processor = cls.get_file_processor(file_processor_name)()
        prompt_builder_class = cls.get_prompt_builder(prompt_builder_name)
        return model_class(model_config, model_name), file_processor, prompt_builder_class

    @classmethod
    def get_available_models(cls) -> List[str]:
        return list(cls.models.keys())
