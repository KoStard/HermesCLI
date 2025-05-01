import logging
import os
import textwrap
from typing import Generator

from hermes.event import Event, MessageEvent
from hermes.interface.commands import Command, CommandParser, CommandRegistry
from hermes.interface.control_panel.base_control_panel import ControlPanel
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.interface.helpers.terminal_coloring import CLIColors
from hermes.message import (
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

logger = logging.getLogger(__name__)


class ChatAssistantControlPanel(ControlPanel):
    def __init__(
        self,
        notifications_printer: CLINotificationsPrinter,
        extra_commands: list = None,
        exa_client=None,
        command_status_overrides: dict = None,
    ):
        super().__init__()
        self.notifications_printer = notifications_printer
        self.exa_client = exa_client
        self._agent_mode = False
        self._commands_parsing_status = True
        
        # Create a command context that will be passed to commands during execution
        self.command_context = ChatAssistantCommandContext(self)
        
        # Get the global command registry
        self.command_registry = CommandRegistry()
        
        # Create the command parser
        self.command_parser = CommandParser()
        
        # Add help content
        self._add_initial_help_content()

        # Register commands with the registry
        self._register_commands()

        # Add any extra commands provided
        if extra_commands:
            for command in extra_commands:
                self._register_command(command)

        # Map of command ID to command status override
        # Possible status values: ON, OFF, AGENT_ONLY
        self._command_status_overrides = (
            command_status_overrides if command_status_overrides is not None else {}
        )

    def _add_initial_help_content(self):
        """Add initial help content about command usage"""
        self._add_help_content(
            textwrap.dedent(
                """
            You are allowed to use the following commands.
            Use them **only** if the user directly asks for them. 
            Understand that they can cause the user frustration and lose trust if used incorrectly. 
            The commands will be programmatically parsed, make sure to follow the instructions precisely when using them. 
            You don't have access to tools other than these. Know that the user doesn't have access to your tools.
            If the content doesn't match these instructions, they will be ignored. 
            The command syntax should be used literally, symbol-by-symbol correctly.
            The commands will be parsed and executed only after you send the full message. You'll receive the responses in the next message.
            
            The command syntax uses a block format with `<<<` and `>>>` delimiters:

            ```
            <<< command_name
            ///section_name
            Section content goes here
            ///another_section
            Another section's content
            >>>
            ```
            
            1. **Direct Commands**:
                - When the user directly asks for something (e.g., "create a file", "make a file"), use the command syntax **without** the `#` prefix. Example:
                    ```
                    <<< create_file
                    ///path
                    example.txt
                    ///content
                    This is the file content.
                    >>>
                    ```
                
            2. **Example Commands**:
                - When the user asks for an **example** of how to use a command (e.g., "how would you create a file?"), use the `#` prefix to indicate it is an example. Example:
                    ```
                    #<<< create_file
                    #///path
                    #example.txt
                    #///content
                    #This is an example file content.
                    #>>>
                    ```
            
            Note that below, you'll have only the "direct commands" listed, but if you are making an example, you can use the example syntax.
            
            **Getting the output of the commands**
            You'll see the results of the command after you send your final message.
            """
            )
        )

        self._add_help_content(
            textwrap.dedent(f"""
            If you are specifying a filepath that has spaces, you should enclose the path in double quotes. For example:
            <<< create_file
            ///path
            "path with spaces/file.txt"
            ///content
            File content goes here
            >>>
            
            While if you are specifying a filepath that doesn't have spaces, you can skip the quotes. For example:
            <<< create_file
            ///path
            path_without_spaces/file.txt
            ///content
            File content goes here
            >>>
            
            **CURRENT WORKING DIRECTORY:** {os.getcwd()}
            All relative paths will be resolved from this location.
            """)
        )

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
            
        # Add help content for agent commands
        self._add_help_content(
            textwrap.dedent(
                """
            **Agent Mode Enabled**
            You are now in the agent mode.
            
            The difference here is that you don't have to finish the task in one reply.
            If the task is too big, you can finish it with multiple messages.
            When you send a message without completing the task, you'll be able to continue with sending your next message, the turn will not move to the user.
            If the task requires information that you don't yet have, or want to check something, you can use the commands, finish your message, 
            the engine will run the commands and you'll see the results, which will allow you to continue with the task in next messages.

            Then after you have confirmed that you finished the task, and you want to show your results to the user, you can use the done command.
            
            You should aim to minimize user interventions until you achieve your task.
            But if it is the case that you lack some important information, don't make assumptions.
            Compile clear, good questions, then use the ask_the_user command to get that information from the user.
            The user will be informed about your command, but preferrably run it early in the process, while they are at the computer.
            
            *Don't see response of command you are executed?*
            You won't receive the response of the commands you use immediately. You need to finish your message, without having the response, to allow the engine to run your commands.
            When you finish your turn, you'll receive a response with the results of the command execution.
            
            CORRECT workflow:
            1. Write your complete message including all needed commands
            2. Finish your message
            3. Wait for response
            4. Process the response in your next message

            INCORRECT workflow:
            ❌ Run command
            ❌ Look for immediate results
            ❌ Run another command
            ❌ Make conclusions before message completion
            
            ⚠️ IMPORTANT: Commands are executed ONLY AFTER your complete message is sent.
            Do NOT expect immediate results while writing your message.
            """
            ),
            is_agent_only=True,
        )

    def render(self) -> str:
        content = []
        content.append(self._render_help_content(is_agent_mode=self._agent_mode))

        commands = self.command_registry.get_all_commands()
        for name, command in sorted(commands.items()):
            command_status_override = self._command_status_overrides.get(name)
            
            # Determine if command should be displayed based on:
            # 1. Status override if present
            # 2. Agent mode requirements (for agent commands)
            is_enabled = False
            
            is_agent_command = name in [
                "done", "ask_the_user", "web_search", "open_url"
            ]
            
            if command_status_override == "OFF":
                is_enabled = False
            elif command_status_override == "ON":
                is_enabled = True
            elif command_status_override == "AGENT_ONLY":
                is_enabled = self._agent_mode
            else:
                if not is_agent_command:
                    is_enabled = True
                elif self._agent_mode:
                    is_enabled = True

            if is_enabled:
                content.append(self._render_command_help(name, command))
        
        return "\n".join(content)

    def break_down_and_execute_message(
        self, message: Message
    ) -> Generator[Event, None, None]:
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
            
        # Extract the raw text content from the message
        content_lines = []
        for line in self._lines_from_message(message):
            yield MessageEvent(
                TextMessage(
                    author="assistant",
                    text=line.rstrip('\n'),
                )
            )
            content_lines.append(line)
        content = "\n".join(content_lines)
            
        # Parse commands using the new command parser
        parse_results = self.command_parser.parse_text(content)
        
        # Sort parse_results by their position in the text
        sorted_results = sorted(
            [r for r in parse_results if r.block_start_line_index is not None],
            key=lambda r: r.block_start_line_index
        )
        
        for result in sorted_results:
            # Check if this is a valid command
            if result.command_name and not result.errors:
                # Execute the command
                command = self.command_registry.get_command(result.command_name)
                if command:
                    self.notifications_printer.print_notification(
                        f"LLM used command: {result.command_name}"
                    )
                    try:
                        for event in command.execute(self.command_context, result.args):
                            yield event
                    except Exception as e:
                        error_msg = f"Command '{result.command_name}' failed: {str(e)}"
                        self.notifications_printer.print_notification(error_msg, CLIColors.RED)
                        yield MessageEvent(
                            TextMessage(
                                author="assistant",
                                text=error_msg,
                                text_role="command_failure",
                            )
                        )
            else:
                # Handle command errors
                error_report = self.command_parser.generate_error_report([result])
                if error_report:
                    self.notifications_printer.print_notification(
                        f"Command parsing error: {error_report}", CLIColors.RED
                    )
                    yield MessageEvent(
                        TextMessage(
                            author="assistant", 
                            text=f"Command parsing error:\n{error_report}",
                            text_role="command_failure"
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
            self.notifications_printer.print_notification(
                f"Unknown command ID: {command_id}", CLIColors.RED
            )
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
        from hermes.interface.commands import CommandHelpGenerator
        help_generator = CommandHelpGenerator()
        return help_generator.generate_help({name: command})
