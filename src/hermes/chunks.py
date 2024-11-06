from hermes.context_providers.base import ContextProvider

class BaseChunk:
    author: str
    permanent: bool

    def __init__(self, author: str, permanent: bool = False):
        self.author = author
        self.permanent = permanent

class AssistantChunk(BaseChunk):
    text: str

    def __init__(self, text: str, permanent: bool = False):
        super().__init__(author="assistant", permanent=permanent)
        self.text = text

class UserTextChunk(BaseChunk):
    text: str

    def __init__(self, text: str, permanent: bool = False):
        super().__init__(author="user", permanent=permanent)
        self.text = text

class UserContextChunk(BaseChunk):
    context_provider: ContextProvider

    def __init__(
        self, 
        context_provider: ContextProvider,
        permanent: bool = False
    ):
        super().__init__(author="user", permanent=permanent)
        self.context_provider = context_provider

class EndOfTurnChunk(BaseChunk):
    """Represents the end of a turn for either the user or assistant"""
    
    def __init__(self, author: str):
        super().__init__(author=author, permanent=False)