from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass(init=False)
class SaveHistoryEvent(EngineCommandEvent):
    filepath: str

    def __init__(self, filepath: str = ""):
        filepath = filepath.strip()
        if not filepath:
            filepath = self._get_default_filepath()
        self.filepath = filepath

    def _get_default_filepath(self) -> str:
        return f"hermes_history_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        orchestrator.notifications_printer.print_notification(f"Saving history to {self.filepath}")
        orchestrator.history.save(self.filepath)
