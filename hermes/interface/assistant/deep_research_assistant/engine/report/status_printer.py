from typing import Optional

from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import (
    FileSystem,
    Node,
)
from hermes.interface.templates.template_manager import TemplateManager


class StatusPrinter:
    """
    Responsible for printing the current status of the research to the console using Mako templates.
    """

    def __init__(self, template_manager: TemplateManager):
        """
        Initialize StatusPrinter.

        Args:
            template_manager: An instance of TemplateManager to render templates.
        """
        self.template_manager = template_manager

    def print_status(
        self,
        problem_defined: bool,
        current_node: Optional[Node],
        file_system: FileSystem,
    ) -> None:
        """Print the current status of the research to STDOUT using a template"""
        context = {
            "problem_defined": problem_defined,
            "current_node": current_node,
            "root_node": file_system.root_node if file_system else None,
            # Pass Node class itself if needed by template helpers like get_status_emoji
            "Node": Node,
        }
        try:
            status_output = self.template_manager.render_template(
                "report/status_report.mako", **context
            )
            # Add a newline before and after the report for better separation
            print(f"\n{status_output}\n")
        except Exception as e:
            print(f"\nError generating status report: {e}\n")
            # Optionally print basic info if template fails
            print("StatusPrinter Fallback:")
            if not problem_defined:
                print("  Status: No problem defined yet")
            elif not current_node:
                print("  Status: No current node")
            else:
                print(f"  Current Problem: {current_node.title}")
                print(
                    f"  Root Node: {file_system.root_node.title if file_system and file_system.root_node else 'N/A'}"
                )
            print("-" * 30)
