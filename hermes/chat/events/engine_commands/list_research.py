from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class ListResearchEvent(EngineCommandEvent):
    """Event to list all research instances"""

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        """List all research instances"""
        if not self._has_research_capability(orchestrator):
            return
            
        try:
            self._list_research_instances(orchestrator)
        except ValueError as e:
            orchestrator.notifications_printer.print_notification(str(e), CLIColors.RED)
    
    def _has_research_capability(self, orchestrator: "ConversationOrchestrator") -> bool:
        """Check if the orchestrator supports research capabilities"""
        if not hasattr(orchestrator.assistant_participant.orchestrator, "list_research_instances"):
            orchestrator.notifications_printer.print_notification(
                "Research management is not available in this mode", 
                CLIColors.RED
            )
            return False
        return True
    
    def _list_research_instances(self, orchestrator: "ConversationOrchestrator") -> None:
        """List all available research instances"""
        instances = orchestrator.assistant_participant.orchestrator.list_research_instances()
        current = self._get_current_research_name(orchestrator)
        
        if not instances:
            orchestrator.notifications_printer.print_notification("No research instances found")
            return
            
        self._display_research_instances(orchestrator, instances, current)
    
    def _get_current_research_name(self, orchestrator: "ConversationOrchestrator") -> str | None:
        """Get name of current research if available"""
        if hasattr(orchestrator.assistant_participant.orchestrator, "get_current_research_name"):
            return orchestrator.assistant_participant.orchestrator.get_current_research_name()
        return None
        
    def _display_research_instances(self, orchestrator: "ConversationOrchestrator", instances: list[str], current: str | None) -> None:
        """Format and display the list of research instances"""
        output = ["Research instances:"]
        for name in instances:
            marker = " (current)" if name == current else ""
            output.append(f"  - {name}{marker}")
        orchestrator.notifications_printer.print_notification("\n".join(output))
