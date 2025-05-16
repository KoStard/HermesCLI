from abc import ABC, abstractmethod

from hermes.chat.interface.assistant.agent.framework.context import AgentInterface
from hermes.chat.interface.assistant.agent.framework.research import Research


class ReportGenerator(ABC):
    @abstractmethod
    def generate_final_report(self, research: Research, interface: AgentInterface, root_completion_message: str | None = None) -> str:
        pass
