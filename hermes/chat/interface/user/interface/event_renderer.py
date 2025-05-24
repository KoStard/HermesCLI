from collections.abc import Generator, Iterable

from hermes.chat.event import Event, MessageEvent, NotificationEvent
from hermes.chat.interface.helpers.cli_notifications import (
    CLIColors,
    CLINotificationsPrinter,
)
from hermes.chat.interface.helpers.terminal_coloring import print_colored_text
from hermes.chat.interface.markdown.markdown_highlighter import MarkdownHighlighter
from hermes.chat.message import Message, TextGeneratorMessage, TextMessage


class EventRenderer:
    def __init__(
        self,
        markdown_highlighter: MarkdownHighlighter | None,
        notifications_printer: CLINotificationsPrinter,
    ):
        self.markdown_highlighter = markdown_highlighter
        self.notifications_printer = notifications_printer

    def render_events(self, events: Generator[Event, None, None]):
        last_author = None
        for event in events:
            if not isinstance(event, MessageEvent):
                self._handle_non_message_event(event)
                continue

            message = event.get_message()
            last_author = self._render_message(message, last_author)
        print()

    def _handle_non_message_event(self, event: Event):
        if isinstance(event, NotificationEvent):
            self.notifications_printer.print_notification(event.text)

    def _render_message(self, message: Message, last_author: str | None) -> str | None:
        if isinstance(message, TextMessage):
            return self._render_text_message(message, last_author)
        elif isinstance(message, TextGeneratorMessage):
            return self._render_text_generator_message(message, last_author)
        return last_author

    def _render_text_message(self, message: TextMessage, last_author: str | None) -> str | None:
        content_for_user = message.get_content_for_user()
        if not content_for_user:
            return last_author

        if self._should_print_author(message.author, last_author):
            self._print_author(message.author)
            last_author = message.author

        self._print_content([content_for_user])
        return last_author

    def _render_text_generator_message(self, message: TextGeneratorMessage, last_author: str | None) -> str | None:
        if self._should_print_author(message.author, last_author):
            self._print_author(message.author)
            last_author = message.author

        self._print_content(message.get_content_for_user())
        return last_author

    def _should_print_author(self, author: str, last_author: str | None) -> bool:
        return author != last_author

    def _print_author(self, author: str):
        print_colored_text(f"\n{author}: ", CLIColors.YELLOW, end="", flush=True)

    def _print_content(self, content_generator: Iterable[str]):
        if self.markdown_highlighter:
            self.markdown_highlighter.process_markdown(chunk for chunk in content_generator)
        else:
            for chunk in content_generator:
                print(chunk, end="", flush=True)
