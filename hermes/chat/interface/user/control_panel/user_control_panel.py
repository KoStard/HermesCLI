from argparse import ArgumentParser, Namespace
from collections.abc import Generator
from typing import Any

from hermes.chat.events.base import Event
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.assistant.chat.control_panel import ChatAssistantControlPanel
from hermes.chat.interface.control_panel import ControlPanel, ControlPanelCommand
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.helpers.peekable_generator import PeekableGenerator
from hermes.chat.interface.user.control_panel.commands import (
    agent_mode_command,
    audio_command,
    budget_command,
    clear_command,
    exa_url_command,
    exit_command,
    focus_subproblem_command,
    fuzzy_select_command,
    image_command,
    image_url_command,
    import_knowledgebase_command,
    list_assistant_commands_command,
    list_research_command,
    llm_commands_execution_command,
    load_history_command,
    once_command,
    pdf_command,
    save_history_command,
    set_assistant_command_status_command,
    switch_research_command,
    text_command,
    textual_file_command,
    textual_files_command,
    thinking_tokens_command,
    tree_command,
    url_command,
    video_command,
)
from hermes.chat.interface.user.control_panel.exa_client import ExaClient
from hermes.chat.messages import Message, TextMessage
from hermes.utils.tree_generator import TreeGenerator


class UserControlPanel(ControlPanel):
    def __init__(
        self,
        *,
        notifications_printer: CLINotificationsPrinter,
        extra_commands: list[ControlPanelCommand],
        exa_client: ExaClient,
        llm_control_panel: ChatAssistantControlPanel,
        is_deep_research_mode=False,
    ):
        super().__init__()
        self.tree_generator = TreeGenerator()
        self.llm_control_panel = llm_control_panel
        self._cli_arguments: set[str] = set()  # Track which arguments were added to CLI
        self.notifications_printer = notifications_printer
        self.exa_client = exa_client
        self.is_deep_research_mode = is_deep_research_mode

        # Register commands
        self._register_all_commands(extra_commands)

    def _register_all_commands(self, extra_commands: list[ControlPanelCommand] | None = None) -> None:
        """Register all commands.

        Args:
            extra_commands: Extra commands to register.
        """
        self._register_command(agent_mode_command.register())
        self._register_command(audio_command.register())
        self._register_command(budget_command.register())
        self._register_command(clear_command.register())
        self._register_command(exa_url_command.register())
        self._register_command(exit_command.register())
        self._register_command(focus_subproblem_command.register())
        self._register_command(fuzzy_select_command.register())
        self._register_command(image_command.register())
        self._register_command(image_url_command.register())
        self._register_command(import_knowledgebase_command.register())
        self._register_command(list_assistant_commands_command.register())
        self._register_command(list_research_command.register())
        self._register_command(llm_commands_execution_command.register())
        self._register_command(load_history_command.register())
        self._register_command(once_command.register())
        self._register_command(pdf_command.register())
        self._register_command(save_history_command.register())
        self._register_command(set_assistant_command_status_command.register())
        self._register_command(switch_research_command.register())
        self._register_command(text_command.register())
        self._register_command(textual_file_command.register())
        self._register_command(textual_files_command.register())
        self._register_command(thinking_tokens_command.register())
        self._register_command(tree_command.register())
        self._register_command(url_command.register())
        self._register_command(video_command.register())

        # Add any extra commands provided
        if extra_commands:
            for command in extra_commands:
                self._register_command(command)

    def render(self):
        results = []
        for command_name in self.commands:
            command = self.commands[command_name]
            if not self._is_command_visible(command):
                continue
            results.append(self._render_command_in_control_panel(command_name))

        return "\n".join(results)

    def _is_command_visible(self, command: ControlPanelCommand) -> bool:
        is_agent_mode = self.llm_control_panel.is_agent_mode
        if not command.visible_from_interface:
            return False
        if self.is_deep_research_mode and not command.is_research_command:
            return False
        if is_agent_mode and not command.is_agent_command:
            return False
        if not is_agent_mode and not command.is_chat_command:  # noqa: SIM103
            return False
        return True

    def extract_and_execute_commands(self, message: Message) -> Generator[Event, None, None]:
        """Extract commands from a message and execute them, yielding resulting events."""
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

    def _create_text_message_event(self, text_content: str) -> tuple[int, MessageEvent]:
        """Create a text message event with priority 0."""
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

    def _parse_command_safely(self, command_label: str, command_parser, command_content: str) -> Any:
        """Safely parse a command, handling exceptions."""
        try:
            return command_parser(command_content)
        except Exception as e:
            self.notifications_printer.print_error(f"Command {command_label} failed: {e}")
            return None

    def _normalize_command_events(self, parsed_command_events: Any) -> list:
        """Normalize command events to a list of events."""
        if parsed_command_events is None:
            return []
        if not isinstance(parsed_command_events, list):
            return [parsed_command_events]
        return parsed_command_events

    def _collect_valid_events(self, command_label: str, events: list, command_priority: int) -> list[tuple[int, Event]]:
        """Validate and collect events with their priorities."""
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
        """Process a single command line and return a list of prioritized events."""
        command_priority = self.commands[command_label].priority
        command_parser = self.commands[command_label].parser
        command_content = self._extract_command_content_in_line(command_label, line)

        parsed_events = self._parse_command_safely(command_label, command_parser, command_content)
        normalized_events = self._normalize_command_events(parsed_events)
        return self._collect_valid_events(command_label, normalized_events, command_priority)

    def _execute_commands_in_priority_order(self, prioritised_events: list[tuple[int, Event]]) -> Generator[Event, None, None]:
        """Execute commands in priority order (highest first) and yield the events."""
        # Sort events by priority (highest to lowest)
        for _, event in sorted(prioritised_events, key=lambda x: -x[0]):
            yield event

    def get_command_labels(self) -> list[str]:
        return [command_label for command_label in self.commands]

    def build_cli_arguments_for_chat(self, parser: ArgumentParser):
        for command_label in self.get_command_labels():
            command = self.commands[command_label]
            if not command.visible_from_cli:
                continue
            if not command.is_chat_command:
                continue
            self._add_command_to_cli_parser(command_label, command, parser, command.default_on_cli)

    def build_cli_arguments_for_simple_agent(self, parser: ArgumentParser):
        for command_label in self.get_command_labels():
            command = self.commands[command_label]
            if not command.visible_from_cli:
                continue
            if not command.is_agent_command:
                continue
            self._add_command_to_cli_parser(command_label, command, parser, command.default_on_cli)

    def build_cli_arguments_for_research(self, parser: ArgumentParser):
        for command_label in self.get_command_labels():
            command = self.commands[command_label]
            if not command.visible_from_cli:
                continue
            if not command.is_research_command:
                continue
            self._add_command_to_cli_parser(command_label, command, parser, command.default_on_cli)

    def _add_command_to_cli_parser(self, command_label: str, command: ControlPanelCommand, parser: ArgumentParser, is_default: bool):
        if command.with_argument:
            if is_default:
                parser.add_argument(
                    command_label[1:],
                    type=str,
                    nargs="*",
                    help=command.description,
                )
                self._cli_arguments.add(command_label[1:])
            else:
                parser.add_argument(
                    "--" + command_label[1:],
                    type=str,
                    action="append",
                    help=command.description,
                )
                self._cli_arguments.add(command_label[1:])
        else:
            # Add flag-only arguments (no values)
            parser.add_argument(
                "--" + command_label[1:],
                action="store_true",
                help=command.description,
            )
            self._cli_arguments.add(command_label[1:])

    def _format_boolean_arg(self, arg: str, value: bool) -> list[str]:
        """Format a boolean CLI argument into command text."""
        if value:
            return [f"/{arg}"]
        return []

    def _format_prompt_arg(self, values: list[str]) -> list[str]:
        """Format prompt arguments into command text."""
        return list(values)

    def _format_standard_arg(self, arg: str, values: list[str]) -> list[str]:
        """Format a standard CLI argument into command text."""
        return [f"/{arg} {v}" for v in values]

    def convert_cli_arguments_to_text(self, args: Namespace) -> str:
        """Convert CLI arguments to text commands for processing."""
        lines = []
        args_dict = vars(args)

        for arg, value in args_dict.items():
            # Skip arguments that are None or not registered
            if value is None or arg not in self._cli_arguments:
                continue

            # Handle different argument types
            if isinstance(value, bool):
                lines.extend(self._format_boolean_arg(arg, value))
            elif arg == "prompt":
                lines.extend(self._format_prompt_arg(value))
            else:
                lines.extend(self._format_standard_arg(arg, value))

        return "\n".join(lines)
