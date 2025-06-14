from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicSectionData
    from hermes.chat.interface.assistant.deep_research.research import Research, ResearchNode
    from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact


class AssistantInterface(ABC):
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

    @abstractmethod
    def collect_artifacts_recursively(
        self, node: "ResearchNode", current_node: "ResearchNode"
    ) -> list[tuple["ResearchNode", "Artifact", bool]]:
        pass
