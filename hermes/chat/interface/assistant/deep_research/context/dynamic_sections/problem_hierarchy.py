from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicSectionData, DynamicSectionRenderer

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class ProblemHierarchyData(DynamicSectionData):
    # Store only the pre-rendered string and target node title
    file_system_hierarchy_str: str
    target_node_title: str

    @staticmethod
    def from_research_node(target_node: "ResearchNode", root_node: "ResearchNode") -> "ProblemHierarchyData":
        """Generate problem hierarchy data from a research node.

        Args:
            target_node: The current node to highlight in the hierarchy

        Returns:
            ProblemHierarchyData with the rendered hierarchy string
        """
        # Build the hierarchy tree
        result = []
        ProblemHierarchyData._build_hierarchy_tree(root_node, result, 0, target_node)
        hierarchy_str = "\n".join(result)

        return ProblemHierarchyData(file_system_hierarchy_str=hierarchy_str, target_node_title=target_node.get_title())

    @staticmethod
    def _build_hierarchy_tree(
        node: "ResearchNode",
        result: list[str],
        indent_level: int,
        current_node: "ResearchNode | None" = None,
    ) -> None:
        """Recursively build the hierarchy tree in XML-like format

        Args:
            node: The current node to process
            result: List to append formatted strings to
            indent_level: Current indentation level
            current_node: The currently active node to highlight
        """
        # Format node information
        artifacts_count = len(node.get_artifacts())
        criteria_met = node.get_criteria_met_count()
        criteria_total = node.get_criteria_total_count()
        node_status = node.get_problem_status().value

        # Check if this is the current node
        is_current = node == current_node
        node_title = node.get_title()

        # Create indentation
        indent = "  " * indent_level

        # Start tag with attributes
        opening_tag = f'{indent}<"{node_title}" '
        opening_tag += f'status="{node_status}" '
        opening_tag += f"criteriaProgress={criteria_met}/{criteria_total} "
        opening_tag += f"depth={node.get_depth_from_root()} "
        opening_tag += f"artifacts={artifacts_count} "

        if is_current:
            opening_tag += 'isCurrent="true" '

        # Get child nodes
        children = node.list_child_nodes()

        # Close the opening tag
        if not children:
            # Self-closing tag if no children
            opening_tag += "/>"
            result.append(opening_tag)
        else:
            # Opening tag with children
            opening_tag += ">"
            result.append(opening_tag)

            # Process children with increased indentation
            for child in children:
                ProblemHierarchyData._build_hierarchy_tree(child, result, indent_level + 1, current_node)

            # Closing tag
            result.append(f'{indent}</"{node_title}">')


# --- Renderer ---
class ProblemHierarchyRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/problem_hierarchy.mako")

    def render(self, data: ProblemHierarchyData, future_changes: int) -> str:
        # Pass the pre-rendered string and title
        context = {
            "file_system_hierarchy_str": data.file_system_hierarchy_str,
            "target_node_title": data.target_node_title,
        }
        return self._render_template(context)
