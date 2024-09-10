from abc import ABC, abstractmethod
import configparser
from typing import Generator

class ChatModel(ABC):
    def __init__(self, config: configparser.ConfigParser, model_tag: str):
        self.config = config
        self.model_tag = model_tag

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def send_message(self, message) -> Generator[str, None, None]:
        pass
    
    @abstractmethod
    def send_history(self, messages) -> Generator[str, None, None]:
        pass
