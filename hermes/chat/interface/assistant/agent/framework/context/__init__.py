from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicSectionData
    from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode


class AgentInterface(ABC):
    @abstractmethod
    def render_problem_defined(
        self,
        research: "Research",
        target_node: "ResearchNode",
        permanent_logs: list[str],
        budget: int | None,
        remaining_budget: int | None,
    ) -> tuple[str, list["DynamicSectionData"]]:
        pass
