from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from hermes.chat.interface.assistant.models.request_builder.base import RequestBuilder
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter


class ChatModel(ABC):
    def __init__(
        self,
        config: dict,
        model_tag: str,
        notifications_printer: CLINotificationsPrinter,
    ):
        self.config = config
        self.model_tag = model_tag
        self.notifications_printer = notifications_printer

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def send_request(self, request: Any) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def get_request_builder(self) -> RequestBuilder:
        pass

    @staticmethod
    @abstractmethod
    def get_provider() -> str:
        pass

    @classmethod
    def get_config_section_name(cls) -> str:
        return cls.get_provider()

    @staticmethod
    @abstractmethod
    def get_model_tags() -> list[str]:
        pass
