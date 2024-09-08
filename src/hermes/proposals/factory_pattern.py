"""
Proposal: Factory Pattern for Model Creation

This proposal suggests using the Factory Pattern to create models, file processors, and prompt builders.

Pros:
1. Centralized model creation logic
2. Easy to add new models without modifying existing code
3. Separates the model creation from its usage
4. Allows for easy extension and configuration of models

Cons:
1. Might introduce additional complexity for simpler use cases
2. Requires careful design to avoid becoming a "god object"

Example implementation:
"""

from abc import ABC, abstractmethod
import configparser
from typing import Dict, Type

# Abstract base classes
class ChatModel(ABC):
    @abstractmethod
    def initialize(self):
        pass

class FileProcessor(ABC):
    @abstractmethod
    def process(self, file_path: str):
        pass

class PromptBuilder(ABC):
    @abstractmethod
    def build(self, prompt: str):
        pass

# Concrete implementations (simplified)
class BedrockModel(ChatModel):
    def initialize(self):
        print("Initializing Bedrock model")

class DefaultFileProcessor(FileProcessor):
    def process(self, file_path: str):
        print(f"Processing file: {file_path}")

class BedrockPromptBuilder(PromptBuilder):
    def build(self, prompt: str):
        print(f"Building Bedrock prompt: {prompt}")

# Factory
class ModelFactory:
    def __init__(self):
        self.models: Dict[str, Type[ChatModel]] = {}
        self.file_processors: Dict[str, Type[FileProcessor]] = {}
        self.prompt_builders: Dict[str, Type[PromptBuilder]] = {}

    def register_model(self, name: str, model_class: Type[ChatModel]):
        self.models[name] = model_class

    def register_file_processor(self, name: str, processor_class: Type[FileProcessor]):
        self.file_processors[name] = processor_class

    def register_prompt_builder(self, name: str, builder_class: Type[PromptBuilder]):
        self.prompt_builders[name] = builder_class

    def create_model(self, name: str, config: configparser.ConfigParser) -> ChatModel:
        model_class = self.models.get(name)
        if not model_class:
            raise ValueError(f"Unknown model: {name}")
        return model_class(config)

    def create_file_processor(self, name: str) -> FileProcessor:
        processor_class = self.file_processors.get(name, DefaultFileProcessor)
        return processor_class()

    def create_prompt_builder(self, name: str) -> PromptBuilder:
        builder_class = self.prompt_builders.get(name)
        if not builder_class:
            raise ValueError(f"Unknown prompt builder: {name}")
        return builder_class()

# Usage
factory = ModelFactory()
factory.register_model("bedrock", BedrockModel)
factory.register_prompt_builder("bedrock", BedrockPromptBuilder)

config = configparser.ConfigParser()
model = factory.create_model("bedrock", config)
file_processor = factory.create_file_processor("default")
prompt_builder = factory.create_prompt_builder("bedrock")

model.initialize()
file_processor.process("example.txt")
prompt_builder.build("Hello, AI!")
