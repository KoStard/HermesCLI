import os
from collections.abc import Generator

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent

from hermes.event import (
    Event,
    MessageEvent,
    NotificationEvent,
    RawContentForHistoryEvent,
)
from hermes.history import History
from hermes.interface import Interface
from hermes.interface.helpers.cli_notifications import (
    CLIColors,
    CLINotificationsPrinter,
)
from hermes.interface.helpers.terminal_coloring import print_colored_text
from hermes.interface.user.command_completer import CommandCompleter
from hermes.interface.markdown.markdown_highlighter import MarkdownHighlighter
from hermes.interface.user.stt_input_handler import STTInputHandler
from hermes.interface.user.user_control_panel import UserControlPanel
from hermes.message import Message, TextGeneratorMessage, TextMessage


class UserInterface(Interface):
    last_messages: list[Message]

    def __init__(
        self,
        *,
        control_panel: UserControlPanel,
        command_completer: CommandCompleter,
        markdown_highlighter: MarkdownHighlighter,
        stt_input_handler: STTInputHandler | None,
        notifications_printer: CLINotificationsPrinter,
        user_input_from_cli: str,
    ):
        self.control_panel = control_panel
        self.command_completer = command_completer
        self.control_panel_has_rendered = False
        self.markdown_highlighter = markdown_highlighter
        self.prompt_toolkit_history = None
        self.tip_shown = False
        self.stt_input_handler = stt_input_handler
        self.notifications_printer = notifications_printer
        self.user_input_from_cli = user_input_from_cli

    def render(self, history_snapshot: list[Message], events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        if not self.control_panel_has_rendered:
            print_colored_text(self.control_panel.render(), CLIColors.GREEN)
            self.control_panel_has_rendered = True

        last_author = None
        for event in events:
            if not isinstance(event, MessageEvent):
                if isinstance(event, NotificationEvent):
                    self.notifications_printer.print_notification(event.text)
                continue

            message = event.get_message()

            if isinstance(message, TextMessage):
                did_author_change = message.author != last_author
                content_for_user = message.get_content_for_user()
                if not content_for_user:
                    continue
                if did_author_change:
                    last_author = message.author
                    self.print_author(message.author)
                if self.markdown_highlighter:
                    self.markdown_highlighter.process_markdown(iter(content_for_user))
                else:
                    print(content_for_user)
            elif isinstance(message, TextGeneratorMessage):
                did_author_change = message.author != last_author
                if did_author_change:
                    last_author = message.author
                    self.print_author(message.author)
                if self.markdown_highlighter:
                    self.markdown_highlighter.process_markdown(message.get_content_for_user())
                else:
                    for chunk in message.get_content_for_user():
                        print(chunk, end="", flush=True)
        print()
        yield from []

    def print_author(self, author: str):
        print_colored_text(f"\n{author}: ", CLIColors.YELLOW, end="", flush=True)

    def get_input(self) -> Generator[Event, None, None]:
        message_source = "terminal"
        if self.user_input_from_cli:
            user_input = self.user_input_from_cli
            self.user_input_from_cli = None
            message_source = "cli"
        elif self.stt_input_handler:
            yield from self._get_user_input_from_speech()
            return
        else:
            user_input = self._get_user_input_from_terminal()

        input_message = TextMessage(author="user", text=user_input)
        yield RawContentForHistoryEvent(input_message)

        sendable_content_present = False

        for event in self.control_panel.break_down_and_execute_message(input_message):
            if isinstance(event, MessageEvent) and (
                message_source != "cli" or (isinstance(event.get_message(), TextMessage) and event.get_message().is_directly_entered)
            ):
                sendable_content_present = True
            yield event

        if not sendable_content_present:
            yield from self.get_input()

    def _get_user_input_from_terminal(self):
        if self.prompt_toolkit_history is None:
            history_dir = "/tmp/hermes/"
            history_file_path = os.path.join(history_dir, "hermes_chat_history.txt")

            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            self.prompt_toolkit_history = FileHistory(history_file_path)

        kb = KeyBindings()

        @kb.add("c-z", eager=True)
        def _(event: KeyPressEvent):
            buffer = event.current_buffer
            buffer.undo()

        # Redo didn't work

        session = PromptSession(
            history=self.prompt_toolkit_history,
            auto_suggest=AutoSuggestFromHistory(),
            multiline=True,
            prompt_continuation=lambda width, line_number, is_soft_wrap: " " * width,
            completer=self.command_completer,
            complete_while_typing=True,
            key_bindings=kb,
        )

        if not self.tip_shown:
            print_colored_text(
                "Tip: Press Escape + Enter to send your message. Press Ctrl+D to exit.",
                CLIColors.YELLOW,
            )
            self.tip_shown = True

        while True:
            try:
                user_input = session.prompt(HTML("<ansiyellow>You: </ansiyellow>"))
                if user_input.strip():
                    break
                print_colored_text("Please enter a non-empty message.", CLIColors.YELLOW)
            except KeyboardInterrupt:
                print_colored_text(
                    "\nInput cleared. Please enter your message or press Ctrl+D to exit.",
                    CLIColors.YELLOW,
                )
                continue

        return user_input

    def _get_user_input_from_speech(self) -> Generator[Event, None, None]:
        text = self.stt_input_handler.get_input()
        yield MessageEvent(TextMessage(author="user", text=text))

    def clear(self):
        pass

    def initialize_from_history(self, history: History):
        pass
