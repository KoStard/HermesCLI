from dataclasses import dataclass
from typing import Optional, List
from hermes.context_providers.base import ContextProvider

@dataclass
class BaseChunk:
    author: str
    permanent: bool = False
    active: bool = False

@dataclass(init=False)
class AssistantChunk(BaseChunk):
    text: str

    def __init__(self, text: str, permanent: bool = False):
        super().__init__(author="assistant", permanent=permanent)
        self.text = text

@dataclass(init=False)
class UserTextChunk(BaseChunk):
    text: str

    def __init__(self, text: str, active: bool = False, permanent: bool = False):
        super().__init__(author="user", active=active, permanent=permanent)
        self.text = text

@dataclass(init=False)
class UserContextChunk(BaseChunk):
    context_provider: ContextProvider
    is_action: bool
    has_acted: bool = False
    override_passive: bool = False

    def __init__(
        self, 
        context_provider: ContextProvider, 
        active: bool = False, 
        permanent: bool = False
    ):
        super().__init__(author="user", active=active, permanent=permanent)
        self.context_provider = context_provider
        self.is_action = context_provider.is_action() 

@dataclass(init=False)
class EndOfTurnChunk(BaseChunk):
    """Represents the end of a turn for either the user or assistant"""
    
    def __init__(self, author: str):
        super().__init__(author=author, permanent=False)