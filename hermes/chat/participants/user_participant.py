from collections.abc import Generator
from typing import TYPE_CHECKING

from hermes.chat.participants.base import Participant

if TYPE_CHECKING:
    from hermes.chat.events import Event
    from hermes.chat.history import History
    from hermes.chat.interface import Orchestrator
    from hermes.chat.interface.user.interface.user_interface import UserOrchestrator


class UserParticipant(Participant):
    def __init__(self, orchestrator: "UserOrchestrator"):
        self.orchestrator = orchestrator

    def consume_events_and_render(self, events: Generator["Event", None, None]):
        self.orchestrator.render(events)

    def get_interface(self) -> "Orchestrator":
        return self.orchestrator

    def get_input_and_run_commands(self) -> Generator["Event", None, None]:
        return self.orchestrator.get_input()

    def get_author_key(self) -> str:
        return "user"

    def clear(self):
        self.orchestrator.clear()

    def initialize_from_history(self, history: "History"):
        self.orchestrator.initialize_from_history(history)

    def get_name(self) -> str:
        return "user"
