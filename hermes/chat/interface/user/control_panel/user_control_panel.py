import os
import shlex
from argparse import ArgumentParser, Namespace
from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any

from hermes.chat.events import (
    AgentModeEvent,
    ClearHistoryEvent,
    CreateResearchEvent,
    DeepResearchBudgetEvent,
    Event,
    ExitEvent,
    ListResearchEvent,
    LLMCommandsExecutionEvent,
    LoadHistoryEvent,
    MessageEvent,
    OnceEvent,
    SaveHistoryEvent,
    SwitchResearchEvent,
    ThinkingLevelEvent,
)
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.helpers.terminal_coloring import CLIColors
from hermes.chat.interface.user.control_panel.exa_client import ExaClient
from hermes.chat.interface.user.control_panel.fuzzy_selector import FuzzyFilesSelector
from hermes.chat.messages import (
    AudioFileMessage,
    EmbeddedPDFMessage,
    ImageMessage,
    ImageUrlMessage,
    Message,
    TextMessage,
    TextualFileMessage,
    UrlMessage,
    VideoMessage,
)
from hermes.utils.file_extension import remove_quotes
from hermes.utils.tree_generator import TreeGenerator

from ...control_panel import ControlPanel, ControlPanelCommand
from ...helpers.peekable_generator import PeekableGenerator


class UserControlPanel(ControlPanel):
    def __init__(
        self,
        *,
        notifications_printer: CLINotificationsPrinter,
        extra_commands: list[ControlPanelCommand],
        exa_client: ExaClient,
        llm_control_panel,
        is_deep_research_mode=False,
    ):
        super().__init__()
        self.tree_generator = TreeGenerator()
        self.llm_control_panel = llm_control_panel
        self._cli_arguments = set()  # Track which arguments were added to CLI
        self.notifications_printer = notifications_printer
        self.exa_client = exa_client
        self.is_deep_research_mode = is_deep_research_mode

        # Register core commands
        self._register_core_commands()

        # Register file sharing commands
        self._register_file_commands()

        # Register history management commands
        self._register_history_commands()

        # Register utility commands
        self._register_utility_commands()

        # Add any extra commands provided
        if extra_commands:
            for command in extra_commands:
                self._register_command(command)

    def _register_core_commands(self):
        """Register basic text and exit commands"""
        self._register_command(
            ControlPanelCommand(
                command_id="text",
                command_label="/text",
                description="Add text to the conversation",
                short_description="Send a text message",
                parser=lambda line: MessageEvent(TextMessage(author="user", text=line, is_directly_entered=True)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="exit",
                command_label="/exit",
                description="Exit the application",
                short_description="Exit Hermes",
                parser=lambda _: ExitEvent(),
                priority=-100,  # Run exit after running any other command
            ),
        )

    def _register_file_commands(self):
        """Register commands for sharing different file types"""
        self._register_command(
            ControlPanelCommand(
                command_id="image",
                command_label="/image",
                description="Add image to the conversation",
                short_description="Share an image file",
                parser=lambda line: MessageEvent(ImageMessage(author="user", image_path=line)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="image_url",
                command_label="/image_url",
                description="Add image from url to the conversation",
                short_description="Share an image via URL",
                parser=lambda line: MessageEvent(ImageUrlMessage(author="user", image_url=line)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="audio",
                command_label="/audio",
                description="Add audio to the conversation",
                short_description="Share an audio file",
                parser=lambda line: MessageEvent(AudioFileMessage(author="user", audio_filepath=line)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="video",
                command_label="/video",
                description="Add video to the conversation",
                short_description="Share a video file",
                parser=lambda line: MessageEvent(VideoMessage(author="user", video_filepath=line)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="pdf",
                command_label="/pdf",
                description="Add pdf to the conversation. After the PDF path, optionally use "
                "{<page_number>, <page_number>:<page_number>, ...} to specify pages.",
                short_description="Share a PDF file",
                parser=lambda line: MessageEvent(EmbeddedPDFMessage.build_from_line(author="user", raw_line=line)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="textual_file",
                command_label="/textual_file",
                description="Add text file to the conversation. Supported: plain textual files, PDFs, DOCs, PowerPoint, Excel, etc.",
                short_description="Share a text-based document",
                parser=lambda line: MessageEvent(TextualFileMessage(author="user", text_filepath=line, textual_content=None)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="textual_files",
                command_label="/textual_files",
                description="Add text file to the conversation. Supported: plain textual files, PDFs, DOCs, PowerPoint, Excel, etc.",
                short_description="Share a text-based document",
                parser=lambda line: MessageEvent(TextualFileMessage(author="user", text_filepath=line, textual_content=None)),
                visible_from_interface=False,
                default_on_cli=True,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="fuzzy_select",
                command_label="/fuzzy_select",
                description="Add text file to the conversation. Supported: plain textual files, PDFs, DOCs, PowerPoint, Excel, etc.",
                short_description="Share a text-based document",
                parser=lambda line: self._parse_fuzzy_select_command(line),
                with_argument=False,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="url",
                command_label="/url",
                description="Add url to the conversation",
                short_description="Share a URL",
                parser=lambda line: MessageEvent(UrlMessage(author="user", url=line)),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="exa_url",
                command_label="/exa_url",
                description="Fetch and add content from a URL using Exa",
                short_description="Fetch URL content with Exa",
                parser=self._parse_exa_url_command,
                visible_from_cli=True,
            ),
        )

    def _register_history_commands(self):
        """Register commands for managing conversation history"""
        self._register_command(
            ControlPanelCommand(
                command_id="clear",
                command_label="/clear",
                description="Clear the conversation history",
                short_description="Clear chat history",
                parser=lambda _: ClearHistoryEvent(),
                priority=99,  # Clear history should be first
                visible_from_cli=False,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="save_history",
                command_label="/save_history",
                description="Save history to a file",
                short_description="Save chat history",
                parser=lambda line: SaveHistoryEvent(line),
                visible_from_cli=False,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="load_history",
                command_label="/load_history",
                description="Load history from a file",
                short_description="Load chat history",
                parser=lambda line: LoadHistoryEvent(line),
                priority=98,
            ),
        )

    def _register_utility_commands(self):
        """Register utility commands like directory tree generation"""
        self._register_command(
            ControlPanelCommand(
                command_id="llm_commands_execution",
                command_label="/llm_commands_execution",
                description="Enable or disable execution of LLM commands (on/off)",
                short_description="Toggle LLM command execution",
                parser=lambda line: LLMCommandsExecutionEvent(enabled=line.strip().lower() == "on"),
            ),
        )
        self._register_command(
            ControlPanelCommand(
                command_id="tree",
                command_label="/tree",
                description="Generate a directory tree",
                short_description="Show directory structure",
                parser=self._parse_tree_command,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="agent_mode",
                command_label="/agent_mode",
                description="Enable or disable agent mode (on/off)",
                short_description="Toggle agent mode",
                parser=lambda line: AgentModeEvent(enabled=line.strip().lower() == "on"),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="once",
                command_label="/once",
                description="Enable or disable once mode - exit after completing current cycle (on/off)",
                short_description="Toggle once mode",
                parser=lambda line: OnceEvent(enabled=line.strip().lower() == "on"),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="list_assistant_commands",
                command_label="/list_assistant_commands",
                description="List all assistant commands and their current status",
                short_description="Show assistant commands",
                parser=self._parse_list_assistant_commands,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="thinking_tokens",
                command_label="/thinking_tokens",
                description="Set the thinking tokens (number)",
                short_description="Set thinking tokens",
                parser=lambda line: ThinkingLevelEvent(count=int(line.strip().lower())),
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="set_deep_research_budget",
                command_label="/set_deep_research_budget",
                description="Set a soft budget limit for Deep Research Assistant (number of message cycles)",
                short_description="Set Deep Research budget",
                parser=self._parse_set_deep_research_budget_command,
                is_deep_research=True,
            ),
        )
        self._register_command(
            ControlPanelCommand(
                command_id="set_assistant_command_status",
                command_label="/set_assistant_command_status",
                description="Set the status of an assistant command (ON/OFF/AGENT_ONLY)",
                short_description="Set assistant command status",
                parser=self._parse_set_assistant_command_status,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="create_research",
                command_label="/create_research",
                description="Create a new research instance and switch to it (Deep Research mode only)",
                short_description="Create new research instance",
                parser=self._parse_create_research_command,
                is_deep_research=True,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="switch_research",
                command_label="/switch_research",
                description="Switch to a different research instance (Deep Research mode only)",
                short_description="Switch research instance",
                parser=self._parse_switch_research_command,
                is_deep_research=True,
            ),
        )

        self._register_command(
            ControlPanelCommand(
                command_id="list_research",
                command_label="/list_research",
                description="List all research instances (Deep Research mode only)",
                short_description="List research instances",
                parser=self._parse_list_research_command,
                with_argument=False,
                is_deep_research=True,
            ),
        )

    def _parse_set_assistant_command_status(self, content: str) -> None:
        """Set the status of an assistant command"""
        if not self.llm_control_panel:
            self.notifications_printer.print_notification("Error: LLM control panel not available", CLIColors.RED)
            return

        try:
            command_id, status = content.strip().split()
            self.llm_control_panel.set_command_override_status(command_id, status)
        except ValueError:
            self.notifications_printer.print_notification(
                "Error: Invalid format. Use: /set_assistant_command_status <command_id> <status>",
                CLIColors.RED,
            )
        return

    def _parse_list_assistant_commands(self, _: str) -> None:
        """List all assistant commands with their current status"""
        if not self.llm_control_panel:
            self.notifications_printer.print_notification("Error: LLM control panel not available", CLIColors.RED)
            return

        overrides = self.llm_control_panel.get_command_override_statuses()
        commands = self.llm_control_panel.get_commands()

        output = ["Assistant Commands:"]
        for cmd in commands:
            overridden_message = ""
            status = "ON" if not cmd.is_agent_command else "AGENT_ONLY"
            if cmd.command_id in overrides:
                status = overrides[cmd.command_id]
                overridden_message = " (Overridden)"
            output.append(f"- {cmd.command_id}: {status}{overridden_message}")

        self.notifications_printer.print_notification("\n".join(output))

        return

    def _parse_set_deep_research_budget_command(self, content: str) -> Event | None:
        """Parse the /set_deep_research_budget command"""
        try:
            budget = int(content.strip())
            if budget <= 0:
                self.notifications_printer.print_notification("Budget must be a positive integer", CLIColors.RED)
                return None
            return DeepResearchBudgetEvent(budget=budget)
        except ValueError:
            self.notifications_printer.print_notification(
                "Invalid budget value. Please provide a positive integer.",
                CLIColors.RED,
            )
            return None

    def _parse_fuzzy_select_command(self, content: str) -> list[Event]:
        """Parse the /fuzzy_select command"""
        try:
            fuzzy_selector = FuzzyFilesSelector()
            absolute_file_paths = fuzzy_selector.select_files(multi=True)
            result_events = []
            for absolute_file_path in absolute_file_paths:
                result_events.append(
                    MessageEvent(
                        TextualFileMessage(
                            author="user",
                            text_filepath=absolute_file_path,
                            textual_content=None,
                        ),
                    ),
                )
            return result_events
        except Exception as e:
            self.notifications_printer.print_notification(f"Error: {e}", CLIColors.RED)
        return []

    def render(self):
        results = []
        for command in self.commands:
            if self.commands[command].is_deep_research and not self.is_deep_research_mode:
                continue
            if not self.commands[command].visible_from_interface:
                continue
            results.append(self._render_command_in_control_panel(command))

        return "\n".join(results)

    def extract_and_execute_commands(self, message: Message) -> Generator[Event, None, None]:
        """Extract commands from a message and execute them, yielding resulting events.
        """
        peekable_generator = PeekableGenerator(self._lines_from_message(message))
        prioritised_backlog = []
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

    def build_cli_arguments(self, parser: ArgumentParser):
        for command_label in self.get_command_labels():
            if self.commands[command_label].visible_from_cli:
                if self.commands[command_label].with_argument:
                    if self.commands[command_label].default_on_cli:
                        parser.add_argument(
                            command_label[1:],
                            type=str,
                            nargs="*",
                            help=self.commands[command_label].description,
                        )
                        self._cli_arguments.add(command_label[1:])
                    else:
                        parser.add_argument(
                            "--" + command_label[1:],
                            type=str,
                            action="append",
                            help=self.commands[command_label].description,
                        )
                        self._cli_arguments.add(command_label[1:])
                else:
                    # Add flag-only arguments (no values)
                    parser.add_argument(
                        "--" + command_label[1:],
                        action="store_true",
                        help=self.commands[command_label].description,
                    )
                    self._cli_arguments.add(command_label[1:])

        parser.add_argument("--prompt", type=str, action="append", help="Prompt for the LLM")
        self._cli_arguments.add("prompt")

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

    def convert_cli_arguments_to_text(self, parser: ArgumentParser, args: Namespace) -> str:
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

    def _parse_create_research_command(self, content: str) -> Event | None:
        """Parse the /create_research command"""
        name = content.strip()
        if not name:
            self.notifications_printer.print_notification("Please provide a name for the new research instance", CLIColors.RED)
            return None

        return CreateResearchEvent(name=name)

    def _parse_switch_research_command(self, content: str) -> Event | None:
        """Parse the /switch_research command"""
        name = content.strip()
        if not name:
            self.notifications_printer.print_notification("Please provide the name of the research instance to switch to", CLIColors.RED)
            return None

        return SwitchResearchEvent(name=name)

    def _parse_list_research_command(self, _: str) -> Event | None:
        """Parse the /list_research command"""
        return ListResearchEvent()

    def _parse_exa_url_command(self, content: str) -> MessageEvent:
        """Parse and execute the /exa_url command"""
        if not self.exa_client:
            raise ValueError("Exa integration not configured - missing EXA_API_KEY in config")

        url = content.strip()
        result = self.exa_client.get_contents(url)[0]
        result_text = result.text
        result_title = result.title
        content_age = (datetime.now(timezone.utc) - datetime.fromisoformat(result.published_date).astimezone(timezone.utc)).days

        if not result_text:
            raise ValueError(f"No content found for URL: {url}")

        if content_age > 7:
            result_text += (
                f"\n\n---\n\nWarning! The snapshot of this website has been last updated {content_age} ago, "
                "it might not be fully up to date"
            )

        return MessageEvent(
            TextualFileMessage(
                author="user",
                name=result_title,
                text_filepath=None,
                file_role="url_content",
                textual_content=result_text,
            ),
        )

    def _parse_tree_command(self, content: str) -> MessageEvent:
        """Parse the /tree command and generate a directory tree.

        Args:
            content: The command content after the label

        Returns:
            MessageEvent with the tree structure
        """
        # Handle quoted paths with spaces
        parts = shlex.split(content)

        path = os.getcwd() if not parts else remove_quotes(parts[0])
        depth = int(parts[1]) if len(parts) > 1 else None

        tree_string = self.tree_generator.generate_tree(path, depth)
        tree_message = TextualFileMessage(
            author="user",
            textual_content=tree_string,
            text_filepath=None,
            file_role="tree_result",
        )
        return MessageEvent(tree_message)
