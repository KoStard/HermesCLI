import logging
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from hermes.chat.events import Event, MessageEvent
from hermes.chat.interface.assistant.chat.command_status_override import ChatAssistantCommandStatusOverride
from hermes.chat.interface.commands.command import Command, CommandRegistry
from hermes.chat.interface.commands.command_parser import CommandParser
from hermes.chat.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.chat.interface.helpers.terminal_coloring import CLIColors
from hermes.chat.interface.user.control_panel.exa_client import ExaClient
from hermes.chat.messages import (
    InvisibleMessage,
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


class ChatAssistantControlPanel:
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
        self._commands_processing_enabled = True

        # Create a command context that will be passed to commands during execution
        self.command_context = ChatAssistantCommandContext(self)

        # Create a command registry instance for this control panel
        self.command_registry = CommandRegistry()

        # Create the command parser, passing the specific registry
        self.command_parser = CommandParser(self.command_registry)

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

    def extract_and_execute_commands(self, message_content: str) -> Generator[Event, None, None]:
        if not self._commands_processing_enabled:
            yield from []
            return
            
        self.command_context.clear_command_outputs()
        sorted_results = self._get_sorted_parse_results(message_content)
        
        # Execute commands
        for result in sorted_results:
            yield from self._process_command_result(result)
        
        # Format and yield outputs
        yield from self._yield_command_outputs()

    def _get_sorted_parse_results(self, message_content: str) -> list:
        """Parse and sort command results by position in text"""
        parse_results = self.command_parser.parse_text(message_content)
        return sorted(
            [r for r in parse_results if r.block_start_line_index is not None],
            key=lambda r: r.block_start_line_index,
        )

    def _process_command_result(self, result) -> Generator[Event, None, None]:
        """Process a single parsed command result"""
        if self._is_valid_command(result):
            yield from self._execute_valid_command(result)
        else:
            self._handle_command_error(result)
        
    def _is_valid_command(self, result) -> bool:
        """Check if this is a valid command with no errors"""
        return result.command_name and not result.errors

    def _execute_valid_command(self, result) -> Generator[Event, None, None]:
        """Execute a valid command and handle any exceptions"""
        command = self.command_registry.get_command(result.command_name)
        if not command:
            return
            
        self.notifications_printer.print_notification(f"LLM used command: {result.command_name}")
        try:
            yield from command.execute(self.command_context, result.args)
        except Exception as e:
            self._record_command_error(result.command_name, result.args, str(e))

    def _handle_command_error(self, result) -> None:
        """Handle errors from invalid commands"""
        error_report = self.command_parser.generate_error_report([result])
        if error_report:
            error_msg = f"Command parsing error: {error_report}"
            self._record_command_error(result.command_name, result.args, error_msg)

    def _record_command_error(self, command_name: str, args: dict, error_message: str) -> None:
        """Record command error to context and display notification"""
        self.command_context.add_command_output(command_name, args, error_message)
        self.notifications_printer.print_notification(error_message, CLIColors.RED)

    def _yield_command_outputs(self) -> Generator[Event, None, None]:
        """Format and yield all command outputs"""
        command_outputs = self.command_context.get_command_outputs()
        if not command_outputs:
            return
            
        command_output_str = self._format_command_outputs(command_outputs)
        yield MessageEvent(InvisibleMessage(
            author="user", 
            text=command_output_str, 
            text_role="command_outputs_and_errors"
        ))

    def _format_command_outputs(self, command_outputs) -> str:
        """Format multiple command outputs into a string"""
        output_strings = []
        for command_name, args, output in command_outputs:
            formatted_args = ", ".join(f"{k}: {str(v)[:100]}" for k, v in args.items())
            output_str = f"""
${"####"} <<< ${command_name}
Arguments: ${formatted_args}
```
{output}
```
"""
            output_strings.append(output_str)
        return "\n".join(output_strings)

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

    def enable_agent_mode(self):
        self._agent_mode = True

    def disable_agent_mode(self):
        self._agent_mode = False

    @property
    def is_agent_mode(self) -> bool:
        return self._agent_mode

    def set_commands_parsing_status(self, status):
        self._commands_processing_enabled = status

    def get_active_commands(self) -> list[Command[Any, Any]]:
        active_commands = []
        commands = self.command_registry.get_all_commands()
        for name, command in sorted(commands.items()):
            if self._is_command_enabled(name, command):
                active_commands.append(command)
        return active_commands
