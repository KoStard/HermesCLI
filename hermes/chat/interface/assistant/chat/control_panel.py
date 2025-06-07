import logging
import os
import textwrap
from collections.abc import Generator
from typing import TYPE_CHECKING

from hermes.chat.events import Event, MessageEvent
from hermes.chat.interface.assistant.chat.command_status_override import ChatAssistantCommandStatusOverride
from hermes.chat.interface.commands.command import Command, CommandRegistry
from hermes.chat.interface.commands.command_parser import CommandParser
from hermes.chat.interface.control_panel import ControlPanel
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.helpers.terminal_coloring import CLIColors
from hermes.chat.interface.user.control_panel.exa_client import ExaClient
from hermes.chat.messages import (
    Message,
    TextGeneratorMessage,
    TextMessage,
)

from .commands import (
    AppendFileCommand,
    AskTheUserCommand,
    ChatAssistantCommandContext,
    CreateFileCommand,
    DoneCommand,
    MarkdownAppendSectionCommand,
    MarkdownUpdateSectionCommand,
    OpenFileCommand,
    OpenUrlCommand,
    PrependFileCommand,
    TreeCommand,
    WebSearchCommand,
)

if TYPE_CHECKING:
    from hermes.mcp.mcp_manager import McpManager

logger = logging.getLogger(__name__)


class ChatAssistantControlPanel(ControlPanel):
    def __init__(
        self,
        notifications_printer: CLINotificationsPrinter,
        extra_commands: list | None,
        exa_client: ExaClient,
        command_status_overrides: dict[str, ChatAssistantCommandStatusOverride] | None,
        mcp_manager: "McpManager",
    ):
        super().__init__()
        self.notifications_printer = notifications_printer
        self.exa_client = exa_client
        self.mcp_manager = mcp_manager
        self._agent_mode = False
        self._commands_parsing_status = True

        # Create a command context that will be passed to commands during execution
        self.command_context = ChatAssistantCommandContext(self)

        # Create a command registry instance for this control panel
        self.command_registry = CommandRegistry()

        # Create the command parser, passing the specific registry
        self.command_parser = CommandParser(self.command_registry)

        # Add help content
        self._add_initial_help_content()

        # Register commands with the registry
        self._register_commands()

        # Add any extra commands provided
        if extra_commands:
            for command in extra_commands:
                self.command_registry.register(command)

        # Map of command ID to command status override
        # Possible status values: ON, OFF, AGENT_ONLY
        self._command_status_overrides: dict[str, ChatAssistantCommandStatusOverride] = (
            command_status_overrides if command_status_overrides is not None else {}
        )

    def update_mcp_commands(self):
        """Registers/updates commands from MCP clients."""
        mcp_commands = self.mcp_manager.create_commands_for_mode("chat")
        for command in mcp_commands:
            self.command_registry.register(command)


    def _register_commands(self):
        """Register all commands with the registry"""
        # File commands
        file_commands = [
            CreateFileCommand(),
            AppendFileCommand(),
            PrependFileCommand(),
        ]

        # Markdown commands
        markdown_commands = [
            MarkdownUpdateSectionCommand(),
            MarkdownAppendSectionCommand(),
        ]

        # Utility commands
        utility_commands = [
            TreeCommand(),
            OpenFileCommand(),
        ]

        # Agent commands
        agent_commands = [
            DoneCommand(),
            AskTheUserCommand(),
            WebSearchCommand(),
            OpenUrlCommand(),
        ]

        # Register all commands
        for command in file_commands + markdown_commands + utility_commands + agent_commands:
            self.command_registry.register(command)

    def render(self) -> str:
        content = []
        content.append(self._render_help_content(is_agent_mode=self._agent_mode))

        commands = self.command_registry.get_all_commands()
        for name, command in sorted(commands.items()):
            if self._is_command_enabled(name, command):
                content.append(self._render_command_help(name, command))

        return "\n".join(content)

    def _is_command_enabled(self, name: str, command: Command) -> bool:
        additional_information = command.get_additional_information()
        is_agent_command = additional_information.get("is_agent_only")

        command_status_override = self._command_status_overrides.get(name)
        if command_status_override == ChatAssistantCommandStatusOverride.OFF:
            return False
        elif command_status_override == ChatAssistantCommandStatusOverride.ON:
            return True
        elif command_status_override == ChatAssistantCommandStatusOverride.AGENT_ONLY:
            return self._agent_mode
        elif not is_agent_command or is_agent_command and self._agent_mode:
            return True
        return False

    def break_down_and_execute_message(self, message: Message) -> Generator[Event, None, None]:
        if not self._commands_parsing_status:
            # If command parsing is disabled, just yield the message as is
            yield MessageEvent(
                TextGeneratorMessage(
                    author="assistant",
                    text_generator=self._lines_from_message(message),
                    is_directly_entered=True,
                )
            )
            return

        accumulated_content = ""

        def _yield_generator_and_accumulate():
            for content in message.get_content_for_user():
                yield content
                nonlocal accumulated_content
                accumulated_content += content

        yield MessageEvent(
            TextGeneratorMessage(
                author="assistant",
                text_generator=_yield_generator_and_accumulate(),
            )
        )

        # Parse commands using the new command parser
        parse_results = self.command_parser.parse_text(accumulated_content)

        # Sort parse_results by their position in the text
        sorted_results = sorted(
            [r for r in parse_results if r.block_start_line_index is not None],
            key=lambda r: r.block_start_line_index,
        )

        for result in sorted_results:
            # Check if this is a valid command
            if result.command_name and not result.errors:
                # Execute the command
                command = self.command_registry.get_command(result.command_name)
                if command:
                    self.notifications_printer.print_notification(f"LLM used command: {result.command_name}")
                    try:
                        yield from command.execute(self.command_context, result.args)
                    except Exception as e:
                        error_msg = f"Command '{result.command_name}' failed: {str(e)}"
                        self.notifications_printer.print_notification(error_msg, CLIColors.RED)
                        yield MessageEvent(
                            TextMessage(
                                author="user",
                                text=error_msg,
                                text_role="command_failure",
                            )
                        )
            else:
                # Handle command errors
                error_report = self.command_parser.generate_error_report([result])
                if error_report:
                    self.notifications_printer.print_notification(f"Command parsing error: {error_report}", CLIColors.RED)
                    yield MessageEvent(
                        TextMessage(
                            author="user",
                            text=f"Command parsing error:\n{error_report}",
                            text_role="command_failure",
                        )
                    )

    def set_command_override_status(self, command_id: str, status: str) -> None:
        """
        Set the override status for a command.

        Args:
            command_id: The unique ID of the command to override
            status: The override status (ON, OFF, or AGENT_ONLY)
        """
        valid_statuses = ["ON", "OFF", "AGENT_ONLY"]
        status = status.upper()

        if status not in valid_statuses:
            self.notifications_printer.print_notification(
                f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}",
                CLIColors.RED,
            )
            return

        if command_id not in self.command_registry.get_command_names():
            self.notifications_printer.print_notification(f"Unknown command ID: {command_id}", CLIColors.RED)
            return

        self._command_status_overrides[command_id] = status

    def get_command_override_statuses(self) -> dict:
        """
        Get all command override statuses.

        Returns:
            dict: Mapping of command IDs to their override status (ON, OFF, or AGENT_ONLY)
        """
        return self._command_status_overrides.copy()

    # All command-specific parsing methods are now handled by Command implementations

    def enable_agent_mode(self):
        self._agent_mode = True

    def disable_agent_mode(self):
        self._agent_mode = False
        # TODO: Inform the assistant that the agent mode was disabled and it might have lost access to some commands

    def set_commands_parsing_status(self, status):
        self._commands_parsing_status = status

    def _render_command_help(self, name: str, command: Command) -> str:
        """Render help for a specific command."""
        from hermes.chat.interface.commands.help_generator import CommandHelpGenerator

        help_generator = CommandHelpGenerator()
        return help_generator.generate_help({name: command})
