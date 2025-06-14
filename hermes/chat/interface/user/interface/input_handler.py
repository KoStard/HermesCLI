import os
from collections.abc import Generator
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent

from hermes.chat.events.base import Event
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.helpers.cli_notifications import CLIColors
from hermes.chat.interface.helpers.terminal_coloring import print_colored_text
from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel
from hermes.chat.interface.user.interface.command_completer.command_completer import CommandCompleter
from hermes.chat.interface.user.interface.message_source import MessageSource
from hermes.chat.messages import TextMessage

if TYPE_CHECKING:
    from hermes.chat.interface.user.interface.stt_input_handler.stt_input_handler import STTInputHandler


class InputHandler:
    def __init__(
        self,
        control_panel: UserControlPanel,
        command_completer: CommandCompleter,
        stt_input_handler: "STTInputHandler | None",
        user_input_from_cli: str,
    ):
        self.control_panel = control_panel
        self.command_completer = command_completer
        self.stt_input_handler = stt_input_handler
        self.user_input_from_cli = user_input_from_cli
        self.prompt_toolkit_history = None
        self.tip_shown = False

    def get_input(self) -> Generator[Event, None, None]:
        message_source = MessageSource.TERMINAL

        if self.user_input_from_cli:
            user_input = self._get_cli_input()
            message_source = MessageSource.CLI
        elif self.stt_input_handler:
            yield from self._get_speech_input()
            return
        else:
            user_input = self._get_terminal_input()

        input_message = TextMessage(author="user", text=user_input)

        yield from self._process_input_message(input_message, message_source)

    def _get_cli_input(self) -> str:
        user_input = self.user_input_from_cli
        self.user_input_from_cli = None
        return user_input

    def _get_speech_input(self) -> Generator[Event, None, None]:
        assert self.stt_input_handler
        text = self.stt_input_handler.get_input()
        yield MessageEvent(TextMessage(author="user", text=text))

    def _get_terminal_input(self) -> str:
        self._initialize_prompt_history()
        session = self._create_prompt_session()
        self._show_tip_if_needed()
        return self._prompt_for_input(session)

    def _initialize_prompt_history(self):
        if self.prompt_toolkit_history is None:
            history_dir = "/tmp/hermes/"
            history_file_path = os.path.join(history_dir, "hermes_chat_history.txt")

            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            self.prompt_toolkit_history = FileHistory(history_file_path)

    def _create_prompt_session(self) -> PromptSession:
        kb = KeyBindings()

        @kb.add("c-z", eager=True)
        def _(event: KeyPressEvent):
            buffer = event.current_buffer
            buffer.undo()

        return PromptSession(
            history=self.prompt_toolkit_history,
            auto_suggest=AutoSuggestFromHistory(),
            multiline=True,
            prompt_continuation=lambda width, line_number, is_soft_wrap: " " * width,
            completer=self.command_completer,
            complete_while_typing=True,
            key_bindings=kb,
        )

    def _show_tip_if_needed(self):
        if not self.tip_shown:
            print_colored_text(
                "Tip: Press Escape + Enter to send your message. Press Ctrl+D to exit.",
                CLIColors.YELLOW,
            )
            self.tip_shown = True

    def _prompt_for_input(self, session: PromptSession) -> str:
        while True:
            try:
                user_input = session.prompt(HTML("<ansiyellow>You: </ansiyellow>"))
                if user_input.strip():
                    return user_input
                print_colored_text("Please enter a non-empty message.", CLIColors.YELLOW)
            except KeyboardInterrupt:
                print_colored_text(
                    "\nInput cleared. Please enter your message or press Ctrl+D to exit.",
                    CLIColors.YELLOW,
                )
                continue

    def _process_input_message(self, input_message: TextMessage, message_source: MessageSource) -> Generator[Event, None, None]:
        sendable_content_present = False

        for event in self.control_panel.extract_and_execute_commands(input_message):
            if self._is_sendable_event(event, message_source):
                sendable_content_present = True
            yield event

        if not sendable_content_present:
            yield from self.get_input()

    def _is_sendable_event(self, event: Event, message_source: MessageSource) -> bool:
        return isinstance(event, MessageEvent) and (
            message_source != MessageSource.CLI
            or (isinstance(event.get_message(), TextMessage) and event.get_message().is_directly_entered)
        )
