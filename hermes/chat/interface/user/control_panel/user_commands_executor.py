from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any

from hermes.chat.events.base import Event
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.helpers.chunks_to_lines import chunks_to_lines
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.helpers.peekable_generator import PeekableGenerator
from hermes.chat.interface.user.control_panel.user_commands_registry import UserCommandsRegistry
from hermes.chat.messages import Message, TextMessage

if TYPE_CHECKING:
    from hermes.chat.interface.user.control_panel.user_control_panel import UserControlPanel


class UserCommandsExecutor:
    def __init__(
        self, *, notifications_printer: CLINotificationsPrinter, commands_registry: UserCommandsRegistry, control_panel: "UserControlPanel"
    ):
        self.notifications_printer = notifications_printer
        self.commands_registry = commands_registry
        self.control_panel = control_panel

    def extract_and_execute_commands(self, message: Message) -> Generator[Event, None, None]:
        peekable_generator = PeekableGenerator(self._lines_from_message(message))
        prioritised_backlog: list[tuple[int, Event]] = []
        current_message_text = ""

        # Process each line from the message
        for line in peekable_generator:
            matching_command = self._line_command_match(line)
            if matching_command:
                # If we have accumulated text, create a message from it
                if current_message_text:
                    prioritised_backlog.append(self._create_text_message_event(current_message_text))
                    current_message_text = ""

                # Process the command and add resulting events to the backlog
                command_results = self._process_command_line(matching_command, line)
                prioritised_backlog.extend(command_results)
            else:
                current_message_text += line

        # Handle any remaining text after processing all lines
        if current_message_text:
            prioritised_backlog.append(self._create_text_message_event(current_message_text))

        # Yield events in priority order
        yield from self._execute_commands_in_priority_order(prioritised_backlog)

    def _lines_from_message(self, message: Message) -> Generator[str, None, None]:
        return chunks_to_lines(message.get_content_for_user())

    def _line_command_match(self, line: str) -> str | None:
        line = line.strip()
        for command_label in self.commands_registry.get_all_commands():
            if line.startswith(command_label + " ") or line == command_label:
                return command_label
        return None

    def _extract_command_content_in_line(self, command_label: str, line: str) -> str:
        return line[len(command_label) :].strip()

    def _create_text_message_event(self, text_content: str) -> tuple[int, MessageEvent]:
        return (
            0,
            MessageEvent(
                TextMessage(
                    author="user",
                    text=text_content,
                    is_directly_entered=True,
                ),
            ),
        )

    def _parse_command_safely(
        self, command_label: str, command_parser: Callable[[str, "UserControlPanel"], Event | None], command_content: str
    ) -> Any:
        try:
            return command_parser(command_content, self.control_panel)
        except Exception as e:
            self.notifications_printer.print_error(f"Command {command_label} failed: {e}")
            return None

    def _normalize_command_events(self, parsed_command_events: Any) -> list:
        if parsed_command_events is None:
            return []
        if not isinstance(parsed_command_events, list):
            return [parsed_command_events]
        return parsed_command_events

    def _collect_valid_events(self, command_label: str, events: list, command_priority: int) -> list[tuple[int, Event]]:
        result_events = []
        for parsed_event in events:
            if not isinstance(parsed_event, Event):
                self.notifications_printer.print_error(
                    f"Command {command_label} returned a non-event object: {parsed_event}",
                )
                continue
            result_events.append((command_priority, parsed_event))
        return result_events

    def _process_command_line(self, command_label: str, line: str) -> list[tuple[int, Event]]:
        command = self.commands_registry.get_command(command_label)
        if not command:
            return []

        command_priority = command.priority
        command_parser = command.parser
        command_content = self._extract_command_content_in_line(command_label, line)

        parsed_events = self._parse_command_safely(command_label, command_parser, command_content)
        normalized_events = self._normalize_command_events(parsed_events)
        return self._collect_valid_events(command_label, normalized_events, command_priority)

    def _execute_commands_in_priority_order(self, prioritised_events: list[tuple[int, Event]]) -> Generator[Event, None, None]:
        # Sort events by priority (highest to lowest)
        for _, event in sorted(prioritised_events, key=lambda x: -x[0]):
            yield event
