from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.base import Event

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass(init=False)
class EngineCommandEvent(Event):
    """Base class for engine commands that can be executed by the conversation orchestrator."""

    @abstractmethod
    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        """Execute the command using the conversation orchestrator."""
        pass
