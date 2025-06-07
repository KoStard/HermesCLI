from abc import ABC, abstractmethod

from hermes.chat.interface.assistant.deep_research.research import Research


class StatusPrinter(ABC):
    @abstractmethod
    def print_status(self, research: Research):
        pass
