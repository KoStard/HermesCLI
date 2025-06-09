from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class FocusSubproblemEvent(EngineCommandEvent):
    """Event to change focus to a specific subproblem"""

    node_id: str

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        """Change focus to the specified subproblem"""
        from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator
        assistant_orchestrator = orchestrator.assistant_participant.orchestrator
        if not isinstance(assistant_orchestrator, DeepResearchAssistantOrchestrator):
            orchestrator.notifications_printer.print_notification("Focus management is not available in this mode", CLIColors.RED)
            return

        engine = assistant_orchestrator.get_engine()
        try:
            if self.node_id == "SHOW_SELECTOR":
                self._handle_selector_mode(engine, orchestrator)
            else:
                self._handle_direct_focus(engine, orchestrator)
        except ValueError as e:
            orchestrator.notifications_printer.print_notification(str(e), CLIColors.RED)

    def _handle_selector_mode(self, engine, orchestrator):
        """Handle focus change using the interactive selector"""
        root_node = engine.get_root_node()
        if not root_node:
            orchestrator.notifications_printer.print_notification("No research project is active", CLIColors.RED)
            return

        from hermes.chat.interface.user.control_panel.subproblem_selector import SubproblemSelector
        selector = SubproblemSelector(root_node)
        selected_node = selector.select_subproblem()

        if selected_node:
            engine.set_focused_node(selected_node.get_id())
            orchestrator.notifications_printer.print_notification(f"Focus changed to: {selected_node.get_title()}")
        else:
            orchestrator.notifications_printer.print_notification("Focus change cancelled")

    def _handle_direct_focus(self, engine, orchestrator):
        """Handle direct focus change by node ID"""
        engine.set_focused_node(self.node_id)
        orchestrator.notifications_printer.print_notification(f"Focus changed to subproblem: {self.node_id}")
