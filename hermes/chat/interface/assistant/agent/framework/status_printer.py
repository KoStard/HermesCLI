from abc import ABC, abstractmethod

from hermes.chat.interface.assistant.agent.framework.research import Research


class StatusPrinter(ABC):
    @abstractmethod
    def print_status(self, research: Research):
        pass
