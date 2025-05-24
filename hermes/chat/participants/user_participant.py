from collections.abc import Generator
from typing import TYPE_CHECKING

from hermes.chat.participants.base import Participant

if TYPE_CHECKING:
    from hermes.chat.events import Event
    from hermes.chat.history import History
    from hermes.chat.interface import Interface
    from hermes.chat.interface.user.interface.user_interface import UserInterface
    from hermes.chat.messages import Message


class UserParticipant(Participant):
    def __init__(self, interface: "UserInterface"):
        self.interface = interface

    def consume_events_and_render(self, history_snapshot: list["Message"], events: Generator["Event", None, None]):
        self.interface.render(history_snapshot, events)

    def get_interface(self) -> "Interface":
        return self.interface

    def get_input_and_run_commands(self) -> Generator["Event", None, None]:
        return self.interface.get_input()

    def get_author_key(self) -> str:
        return "user"

    def clear(self):
        self.interface.clear()

    def initialize_from_history(self, history: "History"):
        self.interface.initialize_from_history(history)

    def get_name(self) -> str:
        return "user"