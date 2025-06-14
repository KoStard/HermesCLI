from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class ListResearchEvent(EngineCommandEvent):
    """Event to list all research instances"""

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        """List all research instances"""
        assistant_orchestrator = orchestrator.assistant_participant.orchestrator
        if not isinstance(assistant_orchestrator, DeepResearchAssistantOrchestrator):
            orchestrator.notifications_printer.print_notification(
                "Research management is not available in this mode",
                CLIColors.RED,
            )
            return

        try:
            self._list_research_instances(orchestrator, assistant_orchestrator)
        except ValueError as e:
            orchestrator.notifications_printer.print_notification(str(e), CLIColors.RED)


    def _list_research_instances(self, orchestrator: "ConversationOrchestrator", assistant_orchestrator: DeepResearchAssistantOrchestrator) -> None:
        """List all available research instances"""
        instances = assistant_orchestrator.list_research_instances()
        current = self._get_current_research_name(orchestrator, assistant_orchestrator)

        if not instances:
            orchestrator.notifications_printer.print_notification("No research instances found")
            return

        self._display_research_instances(orchestrator, instances, current)

    def _get_current_research_name(self, orchestrator: "ConversationOrchestrator", assistant_orchestrator: DeepResearchAssistantOrchestrator) -> str | None:
        """Get name of current research if available"""
        return assistant_orchestrator.get_current_research_name()

    def _display_research_instances(self, orchestrator: "ConversationOrchestrator", instances: list[str], current: str | None) -> None:
        """Format and display the list of research instances"""
        output = ["Research instances:"]
        for name in instances:
            marker = " (current)" if name == current else ""
            output.append(f"  - {name}{marker}")
        orchestrator.notifications_printer.print_notification("\n".join(output))
