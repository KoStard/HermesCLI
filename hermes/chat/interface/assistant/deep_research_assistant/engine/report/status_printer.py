from hermes.chat.interface.assistant.deep_research_assistant.engine.research import Research, ResearchNode
from hermes.chat.interface.templates.template_manager import TemplateManager


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
        current_node: ResearchNode,
        research: Research
    ) -> None:
        """Print the current status of the research to STDOUT using a template"""
        context = {
            "current_node": current_node,
            "root_node": research.get_root_node(),
        }
        status_output = self.template_manager.render_template("report/status_report.mako", **context)
        # Add a newline before and after the report for better separation
        print(f"\n{status_output}\n")
