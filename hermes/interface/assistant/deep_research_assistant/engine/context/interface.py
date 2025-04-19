import textwrap
from typing import List, Optional, Tuple

from hermes.interface.assistant.deep_research_assistant.engine.commands.command import CommandRegistry
from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import FileSystem, Node
from hermes.interface.assistant.deep_research_assistant.engine.commands.commands import register_predefined_commands
from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager
from .hierarchy_formatter import HierarchyFormatter
from .content_truncator import ContentTruncator

register_predefined_commands()


class DeepResearcherInterface:
    """
    Responsible for rendering interface content as strings.
    This class handles all string formatting and presentation logic.
    """

    def __init__(self, file_system: FileSystem):
        self.file_system = file_system
        self.hierarchy_formatter = HierarchyFormatter()
        self.template_manager = TemplateManager()

    def render_problem_defined(
        self, target_node: Node, permanent_logs: List[str], budget: Optional[int], remaining_budget: Optional[int]
    ) -> Tuple[str, List[str]]:
        """
        Render the interface when a problem is defined
        
        Returns:
            A tuple containing:
            - static_content (str): Fixed interface content that doesn't change
            - dynamic_sections (List[str]): List of interface sections that may change, with consistent indices
              
              The order and content of dynamic sections are controlled by the
              `dynamic_sections.mako` template.
        """
        # Render static and dynamic sections separately
        static_section = self._render_static_content(target_node)
        dynamic_sections = self._render_dynamic_sections(
            target_node=target_node,
            permanent_logs=permanent_logs,
            budget=budget,
            remaining_budget=remaining_budget,
        )
        return static_section, dynamic_sections

    def _render_static_content(self, target_node: Node) -> str:
        """Render the static content by rendering the main static.mako template."""
        # Get commands to pass to the template context
        commands = CommandRegistry().get_problem_defined_interface_commands()
        
        context = {
            'target_node': target_node,
            'commands': commands  # Pass the commands dictionary directly
        }
        
        return self.template_manager.render_template("static.mako", **context)

    def _render_dynamic_sections(
        self,
        target_node: Node,
        permanent_logs: List[str],
        budget: Optional[int],
        remaining_budget: Optional[int],
    ) -> List[str]:
        """Render all dynamic sections by rendering the main dynamic_sections.mako template and splitting the result."""
        # --- Prepare context data needed by the main dynamic sections template ---
        # Budget Status Calculation
        budget_status = "GOOD"
        if budget is not None and remaining_budget is not None:
            if remaining_budget <= 0:
                budget_status = "CRITICAL"
            elif remaining_budget <= 10:
                budget_status = "LOW"

        # Artifacts Data (Raw)
        external_files = self.file_system.get_external_files()
        node_artifacts = []
        # Collect artifacts recursively starting from the root to get correct ownership info
        if self.file_system.root_node:
            node_artifacts = self._collect_artifacts_recursively(
                self.file_system.root_node, target_node
            )
        else:
            # Handle case where root_node might not be set yet but problem is defined
            node_artifacts = self._collect_artifacts_recursively(
                target_node, target_node
            )

        # --- Consolidate context for the main template ---
        # Pass raw data and helper objects/classes needed by the template
        context = {
            "target_node": target_node,
            "permanent_logs": permanent_logs,
            "budget": budget,
            "remaining_budget": remaining_budget,
            "budget_status": budget_status,
            "external_files": external_files,
            "node_artifacts": node_artifacts,
            "file_system": self.file_system,
            "hierarchy_formatter": self.hierarchy_formatter,
            "template_manager": self.template_manager,
            "ContentTruncator": ContentTruncator,
        }

        # --- Render the main dynamic sections template ---
        # The template itself will now handle formatting/rendering of internal pieces
        full_dynamic_content = self.template_manager.render_template(
            "dynamic_sections.mako", **context
        )

        # --- Split the rendered content by the separator ---
        # Use a unique separator defined within the template or here
        separator = "<!-- DYNAMIC_SECTION_SEPARATOR -->"
        dynamic_sections = [
            section.strip()
            for section in full_dynamic_content.split(separator)
            if section.strip()  # Remove empty sections resulting from split
        ]

        return dynamic_sections

    # Note: Individual format_* methods for dynamic sections are removed below

    def _collect_artifacts_recursively(
        self, node: Node, current_node: Node
    ) -> List[Tuple[str, str, str, bool]]:
        """
        Recursively collect artifacts from a node and all its descendants.

        Args:
            node: The node to collect artifacts from
            current_node: The node currently being viewed (for visibility checks)

        Returns:
            List of tuples: (owner_title, artifact_name, artifact_content, is_visible_to_current_node)
        """
        artifacts = []
        if not node:
            return artifacts

        # Add this node's artifacts
        for name, artifact in node.artifacts.items():
            is_visible = current_node.visible_artifacts.get(name, False) or artifact.is_external
            artifacts.append(
                (node.title, name, artifact.content, is_visible)
            )

        # Recursively collect artifacts from all subproblems
        for title, subproblem in node.subproblems.items():
            artifacts.extend(
                self._collect_artifacts_recursively(subproblem, current_node)
            )

        return artifacts

    def _generate_command_help(self) -> str:
        """Generate help text for all registered commands by rendering the command_help template."""
        # Get all registered commands suitable for the problem-defined interface
        commands = CommandRegistry().get_problem_defined_interface_commands()
        
        # Render the command help template
        return self.template_manager.render_template(
            "sections/static/command_help.mako", commands=commands
        )
