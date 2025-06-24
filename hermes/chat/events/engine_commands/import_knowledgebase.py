from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent
from hermes.chat.interface.assistant.deep_research.assistant_orchestrator import DeepResearchAssistantOrchestrator
from hermes.chat.interface.helpers.terminal_coloring import CLIColors

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class ImportKnowledgebaseEvent(EngineCommandEvent):
    knowledgebase_path: Path

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        assistant_orchestrator = orchestrator.assistant_participant.orchestrator
        if not isinstance(assistant_orchestrator, DeepResearchAssistantOrchestrator):
            orchestrator.notifications_printer.print_notification("Knowledgebase import is not available in this mode", CLIColors.RED)
            return

        self._import_research_knowledgebase(assistant_orchestrator, orchestrator)

    def _import_research_knowledgebase(
        self, assistant_orchestrator: "DeepResearchAssistantOrchestrator", orchestrator: "ConversationOrchestrator"
    ):
        assistant_orchestrator.get_engine().research.get_knowledge_base().import_entries_from(self.knowledgebase_path)
        orchestrator.notifications_printer.print_notification(f"Knowledgebase imported from {self.knowledgebase_path}")
