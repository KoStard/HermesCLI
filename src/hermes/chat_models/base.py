from abc import ABC, abstractmethod
from typing import Generator

class ChatModel(ABC):
    def __init__(self, config: dict, model_tag: str):
        self.config = config
        self.model_tag = model_tag

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def send_history(self, messages) -> Generator[str, None, None]:
        pass
