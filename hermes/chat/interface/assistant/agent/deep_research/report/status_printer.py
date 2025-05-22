from hermes.chat.interface.assistant.agent.framework.research import Research
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.status_printer import StatusPrinter
from hermes.chat.interface.templates.template_manager import TemplateManager


class StatusPrinterImpl(StatusPrinter):
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
        self.status_emojis = {
            ProblemStatus.CREATED: "🆕",
            ProblemStatus.READY_TO_START: "👀",
            ProblemStatus.PENDING: "⏳",
            ProblemStatus.IN_PROGRESS: "🔍",
            ProblemStatus.FINISHED: "✅",
            ProblemStatus.FAILED: "❌",
            ProblemStatus.CANCELLED: "🚫",
        }

    def _get_status_emoji(self, status: ProblemStatus) -> str:
        """Get an emoji representation of the problem status"""
        return self.status_emojis.get(status, "❓")

    def print_status(self, research: Research):
        """Print the current status of the research to STDOUT using a template"""
        context = {
            "root_node": research.get_root_node(),
            "get_status_emoji": self._get_status_emoji,
        }
        status_output = self.template_manager.render_template("report/status_report.mako", **context)
        # Add a newline before and after the report for better separation
        print(f"\n{status_output}\n")
