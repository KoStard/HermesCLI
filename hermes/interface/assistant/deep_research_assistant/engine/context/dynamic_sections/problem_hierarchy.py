from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import DynamicSectionData, DynamicSectionRenderer

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import (
        FileSystem,
        Node,
    )
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class ProblemHierarchyData(DynamicSectionData):
    # Store only the pre-rendered string and target node title
    file_system_hierarchy_str: str
    target_node_title: str

    @staticmethod
    def from_filesystem_and_node(fs: "FileSystem", target_node: "Node") -> "ProblemHierarchyData":
        hierarchy_str = fs.get_problem_hierarchy(target_node)
        return ProblemHierarchyData(file_system_hierarchy_str=hierarchy_str, target_node_title=target_node.title)


# --- Renderer ---
class ProblemHierarchyRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/problem_hierarchy.mako")

    def render(self, data: ProblemHierarchyData, future_changes: int) -> str:
        # Pass the pre-rendered string and title
        context = {
            "file_system_hierarchy_str": data.file_system_hierarchy_str,
            "target_node_title": data.target_node_title,  # Pass title instead of node
        }
        return self._render_template(context)
