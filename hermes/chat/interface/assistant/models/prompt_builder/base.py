from abc import ABC, abstractmethod

"""
Maybe here we can talk about a tree of prompt pieces, with depths, etc.
"""


class PromptBuilder(ABC):
    @abstractmethod
    def add_text(self, text: str, name: str | None = None, text_role: str | None = None):
        pass

    @abstractmethod
    def compile_prompt(self) -> str:
        pass


class PromptBuilderFactory(ABC):
    @abstractmethod
    def create_prompt_builder(self) -> PromptBuilder:
        pass
