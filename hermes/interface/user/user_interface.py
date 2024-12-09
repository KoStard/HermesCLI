import os
from typing import Generator, Optional

from prompt_toolkit import ANSI, PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings

from hermes_beta.history import History

from hermes_beta.interface.base import Interface
from hermes_beta.interface.control_panel import UserControlPanel
from hermes_beta.interface.user.markdown_highlighter import MarkdownHighlighter
from hermes_beta.interface.user.stt_input_handler import STTInputHandler
from hermes_beta.message import InvisibleMessage, Message, TextGeneratorMessage, TextMessage
from hermes_beta.event import Event, MessageEvent, NotificationEvent
from hermes_beta.interface.helpers import CLINotificationsPrinter, CLIColors, colorize_text, print_colored_text
from hermes_beta.interface.user.command_completer import CommandCompleter


class UserInterface(Interface):
    last_messages: list[Message]
    def __init__(self, *, 
                 control_panel: UserControlPanel, 
                 command_completer: CommandCompleter,
                 markdown_highlighter: MarkdownHighlighter, 
                 stt_input_handler: Optional[STTInputHandler], 
                 notifications_printer: CLINotificationsPrinter,
                 user_input_from_cli: str):
        self.last_messages = []
        self.control_panel = control_panel
        self.command_completer = command_completer
        self.control_panel_has_rendered = False
        self.markdown_highlighter = markdown_highlighter
        self.prompt_toolkit_history = None
        self.tip_shown = False
        self.stt_input_handler = stt_input_handler
        self.notifications_printer = notifications_printer
        self.user_input_from_cli = user_input_from_cli

    def render(self, events: Generator[Event, None, None]) -> Generator[Event, None, None]:
        if not self.control_panel_has_rendered:
            print_colored_text(self.control_panel.render(), CLIColors.GREEN)
            self.control_panel_has_rendered = True

        last_author = None
        for i, event in enumerate(events):
            if i < len(self.last_messages):
                if isinstance(event, MessageEvent) and event.get_message() == self.last_messages[i]:
                    continue
                else:
                    self.notifications_printer.print_error("Messages history has changed, printing the new history")
                    self.last_messages = self.last_messages[:i]

                
            if not isinstance(event, MessageEvent):
                if isinstance(event, NotificationEvent):
                    self.notifications_printer.print_notification(event.text)
                continue

            message = event.get_message()
            if message.author != last_author:
                print()
                last_author = message.author
                print_colored_text(f"{message.author}: ", CLIColors.YELLOW, end="", flush=True)
            self.last_messages.append(message)

            if isinstance(message, TextMessage):
                self.markdown_highlighter.process_markdown(iter(message.get_content_for_user()))
            elif isinstance(message, TextGeneratorMessage):
                self.markdown_highlighter.process_markdown(message.get_content_for_user())
        print()
        yield from []

    def get_input(self) -> Generator[Event, None, None]:
        if self.user_input_from_cli:
            user_input = self.user_input_from_cli
            self.user_input_from_cli = None
        elif self.stt_input_handler:
            return self._get_user_input_from_speech()
        else:
            user_input = self._get_user_input_from_terminal()

        input_message = TextMessage(author="user", text=user_input)

        sendable_content_present = False

        for event in self.control_panel.break_down_and_execute_message(input_message):
            if isinstance(event, MessageEvent):
                self.last_messages.append(event.get_message())
                sendable_content_present = True
            yield event
        
        if not sendable_content_present:
            yield from self.get_input()
    
    def _get_user_input_from_terminal(self):

        if self.prompt_toolkit_history is None:
            history_dir = '/tmp/hermes/'
            history_file_path = os.path.join(history_dir, 'hermes_chat_history.txt')

            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            self.prompt_toolkit_history = FileHistory(history_file_path)

        session = PromptSession(
            history=self.prompt_toolkit_history,
            auto_suggest=AutoSuggestFromHistory(),
            multiline=True,
            prompt_continuation=lambda width, line_number, is_soft_wrap: '.' * width,
            completer=self.command_completer,
            complete_while_typing=True,
        )

        if not self.tip_shown:
            print_colored_text("Tip: Press Escape + Enter to send your message. Press Ctrl+D to exit.", CLIColors.YELLOW)
            self.tip_shown = True

        while True:
            try:
                user_input = session.prompt(HTML('<ansiyellow>You: </ansiyellow>'))
                if user_input.strip():
                    break
                print_colored_text("Please enter a non-empty message.", CLIColors.YELLOW)
            except KeyboardInterrupt:
                print_colored_text("\nInput cleared. Please enter your message or press Ctrl+D to exit.", CLIColors.YELLOW)
                continue
        
        return user_input
    
    def _get_user_input_from_speech(self):
        try:
            text = self.stt_input_handler.get_input()
            yield MessageEvent(TextMessage(author="user", text=text))
            return
        except KeyboardInterrupt as e:
            print(e)
            # TODO: Not working
            print("Recording interrupted")

    
    def clear(self):
        self.last_messages = []

    def initialize_from_history(self, history: History):
        all_messages = history.get_messages()
        user_messages = [message for message in all_messages if message.author == "user"]
        self.last_messages = user_messages
