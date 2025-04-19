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
              
              The sections are ordered as follows:
              0. Header
              1. Permanent Logs
              2. Artifacts
              3. Problem Hierarchy
              4. Criteria
              5. Subproblems
              6. Problem Path Hierarchy
              7. Goal
        """
        # Render static and dynamic sections separately
        static_section = self._render_static_content(target_node)
        dynamic_sections = self._render_dynamic_sections(
            target_node=target_node,
            permanent_logs=permanent_logs,
            budget=budget,
            remaining_budget=remaining_budget
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
        
        return self.template_manager.render_template('static.mako', **context)

    def _render_dynamic_sections(self, target_node: Node, permanent_logs: List[str], budget: Optional[int], remaining_budget: Optional[int]) -> List[str]:
        """Render all dynamic sections"""
        # Create list of dynamic sections by rendering each template
        dynamic_sections = [
            # Section 0: Header
            self._format_header_section(),
            # Section 1: Permanent Logs
            self._format_permanent_log(permanent_logs),
            # Section 2: Budget Information
            self._format_budget_section(budget, remaining_budget),
            # Section 3: Artifacts
            self._format_artifacts_section(False, target_node),
            # Section 4: Problem Hierarchy
            self._format_problem_hierarchy_section(target_node),
            # Section 5: Criteria
            self._format_criteria_section(target_node),
            # Section 6: Subproblems
            self._format_subproblems_section(target_node),
            # Section 7: Problem Path Hierarchy
            self._format_problem_path_hierarchy_section(target_node),
            # Section 8: Goal
            self._format_goal_section(),
        ]

        return dynamic_sections

    def _format_header_section(self) -> str:
        """Render the dynamic header section"""
        return self.template_manager.render_template('sections/dynamic/header.mako')

    def _format_artifacts_section(
        self, external_only: bool, current_node: Optional[Node] = None
    ) -> str:
        """Formats the artifacts section using templates."""
        external_files = self.file_system.get_external_files()
        node_artifacts = []

        if not external_only and current_node:
            # Collect artifacts recursively starting from the root to get correct ownership info
            if self.file_system.root_node:
                node_artifacts = self._collect_artifacts_recursively(
                    self.file_system.root_node, current_node
                )
            else:
                # Handle case where root_node might not be set yet but problem is defined
                node_artifacts = self._collect_artifacts_recursively(
                    current_node, current_node
                )

        # Render the inner content first
        artifacts_content = self.template_manager.render_template(
            'sections/dynamic/artifacts_content.mako',
            external_files=external_files,
            node_artifacts=node_artifacts,
            truncator=ContentTruncator,
        )

        # Render the outer section template, passing the inner content
        return self.template_manager.render_template(
            'sections/dynamic/artifacts.mako', artifacts_content=artifacts_content
        )

    def _format_criteria_section(self, node: Node) -> str:
        """Format criteria section using templates"""
        criteria_content = self.template_manager.render_template(
            'sections/dynamic/criteria_content.mako',
            criteria=node.criteria,
            criteria_done=node.criteria_done,
        )
        return self.template_manager.render_template(
            'sections/dynamic/criteria.mako', criteria_content=criteria_content
        )

    def _format_subproblems_section(self, node: Node) -> str:
        """Format subproblems section using templates"""
        subproblems_content = self.hierarchy_formatter.format_subproblems(node)
        return self.template_manager.render_template(
            'sections/dynamic/subproblems.mako', subproblems_content=subproblems_content
        )

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
            artifacts.extend(self.collect_artifacts_recursively(subproblem, current_node))

        return artifacts

    def _format_permanent_log(self, permanent_logs: list) -> str:
        """Format permanent log section using templates"""
        permanent_log_content = (
            "\n".join(f"- {entry}" for entry in permanent_logs)
            if permanent_logs
            else "No history entries yet."
        )
        return self.template_manager.render_template(
            'sections/dynamic/permanent_logs.mako',
            permanent_log_content=permanent_log_content,
        )

    def _format_problem_hierarchy_section(self, node: Node) -> str:
        """Format the problem hierarchy section using templates"""
        problem_hierarchy_content = self.file_system.get_problem_hierarchy(node)
        return self.template_manager.render_template(
            'sections/dynamic/problem_hierarchy.mako',
            problem_hierarchy=problem_hierarchy_content,
        )

    def _format_problem_path_hierarchy_section(self, node: Node) -> str:
        """Format the problem path hierarchy section using templates"""
        problem_path_hierarchy_content = (
            self.hierarchy_formatter.format_problem_path_hierarchy(node)
        )
        return self.template_manager.render_template(
            'sections/dynamic/problem_path_hierarchy.mako',
            problem_path_hierarchy=problem_path_hierarchy_content,
        )

    def _format_goal_section(self) -> str:
        """Render the goal section using templates"""
        return self.template_manager.render_template('sections/dynamic/goal.mako')

    def _generate_command_help(self) -> str:
        """Generate help text for all registered commands by rendering the command_help template."""
        # Get all registered commands suitable for the problem-defined interface
        commands = CommandRegistry().get_problem_defined_interface_commands()
        
        # Render the command help template
        return self.template_manager.render_template(
            'sections/static/command_help.mako', 
            commands=commands
        )

    def _format_budget_section(self, total, remaining) -> str:
        """Format the budget section using templates"""
        budget_status = "GOOD"
        if total is not None and remaining is not None:
            if remaining <= 0:
                budget_status = "CRITICAL"
            elif remaining <= 10:
                budget_status = "LOW"

        return self.template_manager.render_template(
            'sections/dynamic/budget.mako',
            total=total,
            remaining=remaining,
            budget_status=budget_status,
        )
