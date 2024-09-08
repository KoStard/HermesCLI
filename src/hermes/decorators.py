from .registry import ModelRegistry

def register_model(name: str, file_processor: str, prompt_builder: str):
    return ModelRegistry.register_model(name, file_processor, prompt_builder)

register_file_processor = ModelRegistry.register_file_processor
register_prompt_builder = ModelRegistry.register_prompt_builder
