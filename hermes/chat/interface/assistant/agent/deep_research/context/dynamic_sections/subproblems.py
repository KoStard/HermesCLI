from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicSectionData, DynamicSectionRenderer

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Primitive Data Structure ---
@dataclass(frozen=True)
class PrimitiveSubproblemData:
    """Immutable, primitive representation of a Node's subproblem summary."""

    # Fields needed for summary rendering parity
    title: str
    problem_definition: str
    criteria: tuple[str, ...]
    criteria_done: tuple[bool, ...]
    artifacts_count: int
    status_label: str
    criteria_status: str  # Combined criteria met/total string

    @staticmethod
    def from_node(node: "ResearchNode") -> "PrimitiveSubproblemData":
        return PrimitiveSubproblemData(
            title=node.get_title(),
            problem_definition=node.get_problem().content,
            criteria=tuple(e.content for e in node.get_criteria()),
            criteria_done=tuple(e.is_completed for e in node.get_criteria()),
            artifacts_count=len(node.get_artifacts()),
            status_label=node.get_problem_status().name,
            criteria_status=f"[{node.get_criteria_met_count()}/{node.get_criteria_total_count()} criteria met]",
        )


# --- Data ---
@dataclass(frozen=True)
class SubproblemsSectionData(DynamicSectionData):
    # Store primitive representations of subproblems
    subproblems: tuple[PrimitiveSubproblemData, ...]

    @staticmethod
    def from_node(target_node: "ResearchNode") -> "SubproblemsSectionData":
        subproblem_data = tuple(
            PrimitiveSubproblemData.from_node(subproblem)
            for subproblem in target_node.list_child_nodes()
        )
        return SubproblemsSectionData(subproblems=subproblem_data)


# --- Renderer ---
class SubproblemsSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/subproblems.mako")

    def render(self, data: SubproblemsSectionData, future_changes: int) -> str:
        # Pass the primitive tuple of subproblem data
        context = {"subproblems_data": data.subproblems}  # Tuple[PrimitiveSubproblemData]
        return self._render_template(context)
