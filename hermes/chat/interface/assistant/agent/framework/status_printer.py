from abc import ABC, abstractmethod

from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode


class StatusPrinter(ABC):
    @abstractmethod
    def print_status(
        self,
        current_node: ResearchNode,
        research: Research
    ):
        pass
