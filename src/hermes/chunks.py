from dataclasses import dataclass
from typing import Optional, List
from hermes.context_providers.base import ContextProvider

@dataclass
class BaseChunk:
    author: str
    permanent: bool = False

@dataclass(init=False)
class AssistantChunk(BaseChunk):
    text: str

    def __init__(self, text: str, permanent: bool = False):
        super().__init__(author="assistant", permanent=permanent)
        self.text = text

@dataclass(init=False)
class UserTextChunk(BaseChunk):
    text: str

    def __init__(self, text: str, permanent: bool = False):
        super().__init__(author="user", permanent=permanent)
        self.text = text

@dataclass(init=False)
class UserContextChunk(BaseChunk):
    context_provider: ContextProvider

    def __init__(
        self, 
        context_provider: ContextProvider,
        permanent: bool = False
    ):
        super().__init__(author="user", permanent=permanent)
        self.context_provider = context_provider

@dataclass(init=False)
class EndOfTurnChunk(BaseChunk):
    """Represents the end of a turn for either the user or assistant"""
    
    def __init__(self, author: str):
        super().__init__(author=author, permanent=False)