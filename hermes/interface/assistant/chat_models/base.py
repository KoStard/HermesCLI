from abc import ABC, abstractmethod
from typing import Generator

from hermes.interface.assistant.prompt_builder.base import PromptBuilder
from hermes.interface.assistant.request_builder.base import RequestBuilder
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter

class ChatModel(ABC):
    def __init__(self, config: dict, model_tag: str, notifications_printer: CLINotificationsPrinter):
        self.config = config
        self.model_tag = model_tag
        self.notifications_printer = notifications_printer

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def send_request(self, request: any) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def get_request_builder(self) -> RequestBuilder:
        pass

    @staticmethod
    @abstractmethod
    def get_provider() -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_model_tags() -> list[str]:
        pass
