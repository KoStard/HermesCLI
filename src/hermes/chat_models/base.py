from abc import ABC, abstractmethod
import configparser
from typing import Generator

class ChatModel(ABC):
    def __init__(self, config: configparser.ConfigParser):
        self.config = config

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def send_message(self, message) -> Generator[str, None, None]:
        pass
