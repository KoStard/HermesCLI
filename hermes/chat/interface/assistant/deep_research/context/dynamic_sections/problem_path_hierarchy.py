from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicSectionData, DynamicSectionRenderer
from hermes.chat.interface.assistant.deep_research.research import ResearchNode

from .subproblems import PrimitiveSubproblemData

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Primitive Data Structure ---
@dataclass(frozen=True)
class PrimitiveNodePathData:
    """Immutable, primitive representation of a Node in a hierarchy path."""

    # Fields needed for path rendering parity
    title: str
    problem_definition: str
    criteria: tuple[str, ...]
    criteria_done: tuple[bool, ...]
    artifacts_count: int
    depth: int
    is_current: bool
    # Include sibling subproblems not in the direct path
    sibling_subproblems: tuple[PrimitiveSubproblemData, ...] = field(default_factory=tuple)

    @staticmethod
    def from_node(
        node: "ResearchNode",
        is_current: bool,
        sibling_subproblems_data: tuple[PrimitiveSubproblemData, ...] = (),
    ) -> "PrimitiveNodePathData":
        return PrimitiveNodePathData(
            title=node.get_title(),
            problem_definition=node.get_problem().content,
            criteria=tuple(e.content for e in node.get_criteria()),
            criteria_done=tuple(e.is_completed for e in node.get_criteria()),
            artifacts_count=len(node.get_artifacts()),
            depth=node.get_depth_from_root(),
            is_current=is_current,
            sibling_subproblems=sibling_subproblems_data,
        )


# --- Data ---
@dataclass(frozen=True)
class ProblemPathHierarchyData(DynamicSectionData):
    # Store primitive representations of nodes in the path
    path_nodes: tuple[PrimitiveNodePathData, ...]

    @staticmethod
    def from_parent_chain(parent_chain: list["ResearchNode"], current_node: "ResearchNode") -> "ProblemPathHierarchyData":
        path_data_list = []
        for i, node in enumerate(parent_chain):
            is_current_node_in_path = node == current_node
            next_node_in_path = parent_chain[i + 1] if i + 1 < len(parent_chain) else None

            # Collect data for sibling subproblems (those not the next node in the path)
            sibling_data = []
            for sub_node in node.list_child_nodes():
                if sub_node != next_node_in_path:
                    # Use the factory from subproblems.py
                    sibling_data.append(PrimitiveSubproblemData.from_node(sub_node))

            # Create the PrimitiveNodePathData including siblings
            # Use the factory defined in this file
            node_path_data = PrimitiveNodePathData.from_node(
                node=node,
                is_current=is_current_node_in_path,
                sibling_subproblems_data=tuple(sibling_data),
            )
            path_data_list.append(node_path_data)

        return ProblemPathHierarchyData(path_nodes=tuple(path_data_list))


# --- Renderer ---
class ProblemPathHierarchyRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/problem_path_hierarchy.mako")

    def render(self, data: ProblemPathHierarchyData, future_changes: int) -> str:
        # Pass the primitive tuple of path node data
        context = {"path_nodes_data": data.path_nodes}  # Tuple[PrimitiveNodePathData]
        return self._render_template(context)
