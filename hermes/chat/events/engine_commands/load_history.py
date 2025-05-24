import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass(init=False)
class LoadHistoryEvent(EngineCommandEvent):
    filepath: str

    def __init__(self, filepath: str):
        filepath = filepath.strip()
        self.filepath = self._verify_filepath(filepath)

    def _verify_filepath(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            raise ValueError(f"Filepath {filepath} does not exist")
        return filepath

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        orchestrator.notifications_printer.print_notification(f"Loading history from {self.filepath}")
        orchestrator.history.load(self.filepath)
        for participant in orchestrator.participants:
            participant.initialize_from_history(orchestrator.history)