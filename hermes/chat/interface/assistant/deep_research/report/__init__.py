from abc import ABC, abstractmethod

from hermes.chat.interface.assistant.deep_research.context import AssistantInterface
from hermes.chat.interface.assistant.deep_research.research import Research


class ReportGenerator(ABC):
    @abstractmethod
    def generate_final_report(self, research: Research, interface: AssistantInterface, root_completion_message: str | None = None) -> str:
        pass
