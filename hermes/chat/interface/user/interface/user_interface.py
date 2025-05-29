from collections.abc import Generator
from typing import TYPE_CHECKING

from hermes.chat.events import Event
from hermes.chat.history import History
from hermes.chat.interface import Interface
from hermes.chat.interface.helpers.cli_notifications import CLIColors, CLINotificationsPrinter
from hermes.chat.interface.helpers.terminal_coloring import print_colored_text
from hermes.chat.interface.markdown.markdown_highlighter import MarkdownHighlighter
from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel
from hermes.chat.interface.user.interface.command_completer.command_completer import CommandCompleter
from hermes.chat.interface.user.interface.event_renderer import EventRenderer
from hermes.chat.interface.user.interface.input_handler import InputHandler
from hermes.chat.messages import Message

if TYPE_CHECKING:
    from hermes.chat.interface.user.interface.stt_input_handler.stt_input_handler import STTInputHandler


class UserInterface(Interface):
    def __init__(
        self,
        *,
        control_panel: UserControlPanel,
        command_completer: CommandCompleter,
        markdown_highlighter: MarkdownHighlighter | None,
        stt_input_handler: "STTInputHandler | None",
        notifications_printer: CLINotificationsPrinter,
        user_input_from_cli: str,
    ):
        self.control_panel = control_panel
        self.control_panel_has_rendered = False
        self.event_renderer = EventRenderer(markdown_highlighter, notifications_printer)
        self.input_handler = InputHandler(
            control_panel, command_completer, stt_input_handler, user_input_from_cli
        )

    def render(self, history_snapshot: list[Message], events: Generator[Event, None, None]):
        self.event_renderer.render_events(events)

    def get_input(self) -> Generator[Event, None, None]:
        self._render_control_panel_if_needed()
        yield from self.input_handler.get_input()

    def _render_control_panel_if_needed(self):
        if not self.control_panel_has_rendered:
            print_colored_text(self.control_panel.render(), CLIColors.GREEN)
            self.control_panel_has_rendered = True

    def clear(self):
        pass

    def initialize_from_history(self, history: History):
        pass
