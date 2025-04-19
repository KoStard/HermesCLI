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
        # Prepare context for the base template
        template_context = {
            'static_content': self._render_static_content(),
            'target_node': target_node,
            'budget': budget,
            'remaining_budget': remaining_budget
        }
        
        # Render the complete interface using the base template
        static_section = self.template_manager.render_template('static.mako', **template_context)
        dynamic_sections = self._render_dynamic_sections(
            target_node=target_node,
            permanent_logs=permanent_logs,
            budget=budget,
            remaining_budget=remaining_budget
        )
        return static_section, dynamic_sections

    def _render_static_content(self) -> str:
        """Render all static content sections"""
        sections = []
        for template_name in ['introduction', 'mission', 'interface_structure', 'commands', 'planning', 'budget']:
            template_path = f'sections/static/{template_name}.mako'
            context = {}
            if template_name == 'commands':
                context['command_help'] = self._generate_command_help()
            sections.append(self.template_manager.render_template(template_path, **context))
        return '\n\n'.join(sections)

    def _render_dynamic_sections(self, target_node: Node, permanent_logs: List[str], budget: Optional[int], remaining_budget: Optional[int]) -> List[str]:
        """Render all dynamic sections"""
        # Format all the sections first
        permanent_log_section = self._format_permanent_log(permanent_logs)
        artifacts_section = self._format_artifacts_section(False, target_node)
        problem_hierarchy = self.file_system.get_problem_hierarchy(target_node)
        criteria_section = self._format_criteria(target_node)
        subproblems_sections = self._format_subproblems(target_node)
        problem_path_hierarchy_section = self._format_problem_path_hierarchy(target_node)

        # Create list of dynamic sections
        dynamic_sections = [
            # Section 0: Header
            """# Deep Research Interface (Dynamic Section)
Here goes the dynamic section of the interface. This contains key information that changes as you work.
When you first join a problem, you'll see all sections. After that, you'll only receive the sections 
that have changed since your last message.""",
            
            # Section 1: Permanent Logs
            permanent_log_section,
            
            # Section 2: Budget Information
            self._format_budget_section(budget, remaining_budget),
            
            # Section 3: Artifacts
            f"""======================
# Artifacts (All Problems)

{artifacts_section}""",
            
            # Section 3: Problem Hierarchy
            f"""======================
## Problem Hierarchy (short)
Notice: The problem hierarchy includes all the problems in the system and their hierarchical relationship, with some metadata. 
The current problem is marked with isCurrent="true".

{problem_hierarchy}""",
            
            # Section 4: Criteria
            f"""## Criteria of Definition of Done
{criteria_section}""",
            
            # Section 5: Subproblems
            f"""## Subproblems of the current problem
{subproblems_sections}""",
            
            # Section 6: Problem Path Hierarchy
            f"""## Problem Path Hierarchy (from root to current)
{problem_path_hierarchy_section}""",
            
            # Section 7: Goal
            """## Goal
Ask yourself, what does the user want?
Your fundamental goal is to help/solve the root problem through solving your assigned problem. Stay frugal, don't focus on the unnecessary details that won't benefit the root problem. But don't sacrifice on quality. If you find yourself working on something that's not worth the effort, mark as done and write it in the report.
Remember, we work backwards from the root problem.

# So, what's your message to the engine?"""
        ]
        
        return dynamic_sections

    def _format_artifacts_section(
        self, external_only: bool, current_node: Optional[Node] = None
    ) -> str:
        """Formats the artifacts section, optionally including only external files."""
        external_files = self.file_system.get_external_files()
        node_artifacts = []

        if not external_only and current_node:
            # Collect artifacts recursively starting from the root to get correct ownership info
            if self.file_system.root_node:
                node_artifacts = self.collect_artifacts_recursively(
                    self.file_system.root_node,
                    current_node
                )
            else:
                # Handle case where root_node might not be set yet but problem is defined
                node_artifacts = self.collect_artifacts_recursively(current_node, current_node)

        return self.template_manager.render_template(
            'sections/dynamic/artifacts_content.mako',
            external_files=external_files,
            node_artifacts=node_artifacts,
            truncator=ContentTruncator
        )

    def _format_criteria(self, node: Node) -> str:
        """Format criteria for display"""
        return self.template_manager.render_template(
            'sections/dynamic/criteria_content.mako',
            criteria=node.criteria,
            criteria_done=node.criteria_done
        )

    def _format_subproblems(self, node: Node) -> str:
        """Format breakdown structure for display"""
        return self.template_manager.render_template(
            'sections/dynamic/subproblems.mako',
            subproblems_content=self.hierarchy_formatter.format_subproblems(node)
        )

    def collect_artifacts_recursively(
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
        """Format permanent history for display"""
        return self.template_manager.render_template(
            'sections/dynamic/permanent_logs.mako',
            permanent_log_content="\n".join(f"- {entry}" for entry in permanent_logs) if permanent_logs else "No history entries yet."
        )

    def _format_problem_path_hierarchy(self, node: Node) -> str:
        """Format the hierarchical path from root to current node for display"""
        return self.hierarchy_formatter.format_problem_path_hierarchy(node)

    def _generate_command_help(self) -> str:
        """Generate help text for all registered commands"""
        # Get all registered commands suitable for the problem-defined interface
        commands = CommandRegistry().get_problem_defined_interface_commands()

        # Generate command help text
        result = []
        for name, cmd in sorted(commands.items()):
            # Command header with name
            command_text = f"<<< {name}"

            # Add sections
            for section in cmd.sections:
                command_text += f"\n///{section.name}"
                if section.allow_multiple:
                    command_text += " (multiple allowed)"
                if section.help_text:
                    command_text += f"\n{section.help_text}"
                else:
                    command_text += f"\nYour {section.name} here"

            # Command footer
            command_text += "\n>>>"

            # Add help text if available
            if cmd.help_text:
                command_text += "\n" + "\n".join(
                    "; " + line for line in cmd.help_text.split("\n")
                )

            result.append(command_text)

        return "\n\n".join(result)
        
    def _format_budget_section(self, total, remaining) -> str:
        """Format the budget section for display"""
        # Get budget info from the engine
        if total is None or remaining is None:
            return "======================\n# Budget Information\nNo budget has been set."
            
        used = total - remaining
        
        budget_status = "GOOD"
        if remaining <= 10:
            budget_status = "LOW"
        if remaining <= 0:
            budget_status = "CRITICAL"
        
        budget_section = f"""======================
# Budget Information
- Total budget: {total} message cycles
- Used: {used} message cycles
- Remaining: {remaining} message cycles
- Status: {budget_status}

"""
        if budget_status == "CRITICAL":
            budget_section += """⚠️ **BUDGET CRITICAL** ⚠️
You are operating on borrowed time. Please finalize your work immediately and submit your findings.
"""
        elif budget_status == "LOW":
            budget_section += """⚠️ **BUDGET WARNING** ⚠️
Budget is running low. Please prioritize the most important tasks and consider wrapping up soon.
"""
        else:
            budget_section += "Please be mindful of the budget when planning your research strategy."
            
        return budget_section
