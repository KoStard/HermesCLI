from dataclasses import dataclass
from typing import Tuple, TYPE_CHECKING

from .base import DynamicSectionData, DynamicSectionRenderer

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import Node
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager


# --- Primitive Data Structure ---
@dataclass(frozen=True)
class PrimitiveSubproblemData:
    """Immutable, primitive representation of a Node's subproblem summary."""
    # Fields needed for summary rendering parity
    title: str
    problem_definition: str
    criteria: Tuple[str, ...]
    criteria_done: Tuple[bool, ...]
    artifacts_count: int
    status_emoji: str
    status_label: str
    criteria_status: str # Combined criteria met/total string

    @staticmethod
    def from_node(node: "Node") -> "PrimitiveSubproblemData":
        return PrimitiveSubproblemData(
            title=node.title,
            problem_definition=node.problem_definition,
            criteria=tuple(node.criteria),
            criteria_done=tuple(node.criteria_done),
            artifacts_count=len(node.artifacts),
            status_emoji=node.get_status_emoji(),
            status_label=node.get_status_label(),
            criteria_status=node.get_criteria_status()
        )


# --- Data ---
@dataclass(frozen=True)
class SubproblemsSectionData(DynamicSectionData):
    # Store primitive representations of subproblems
    subproblems: Tuple[PrimitiveSubproblemData, ...]

    @staticmethod
    def from_node(target_node: "Node") -> "SubproblemsSectionData":
        subproblem_data = tuple(
            PrimitiveSubproblemData.from_node(subproblem)
            for title, subproblem in sorted(target_node.subproblems.items()) # Sort for consistent order
        )
        return SubproblemsSectionData(subproblems=subproblem_data)


# --- Renderer ---
class SubproblemsSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/subproblems.mako")

    def render(self, data: SubproblemsSectionData, future_changes: int) -> str:
        # Pass the primitive tuple of subproblem data
        context = {"subproblems_data": data.subproblems} # Tuple[PrimitiveSubproblemData]
        return self._render_template(context)
