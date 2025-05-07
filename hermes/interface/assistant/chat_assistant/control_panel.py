import logging
import os
import textwrap
from collections.abc import Generator

from hermes.event import Event, MessageEvent
from hermes.interface.commands.command import Command, CommandRegistry
from hermes.interface.commands.command_parser import CommandParser
from hermes.interface.control_panel import ControlPanel
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
                self.command_registry.register(command)

        # Map of command ID to command status override
        # Possible status values: ON, OFF, AGENT_ONLY
        self._command_status_overrides = command_status_overrides if command_status_overrides is not None else {}

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
            
            Use commands exactly as shown, with correct syntax. Closing tags are mandatory, otherwise parsing will break. 
            The commands should start from an empty line, from first symbol in the line. 
            Don't put anything else in the lines of the commands.
            
            You write down the commands you want to send in this interface.
            
            ⚠️ **IMPORTANT**: Commands are processed AFTER you send your message. Finish your message, read the responses, 
            then consider the next steps.
            
            Notice that we use <<< for opening the commands, >>> for closing, and /// for arguments. Make sure you use the exact syntax.

            ```
            <<< command_name
            ///section_name
            Section content goes here
            ///another_section
            Another section's content
            >>>
            ```
            
            1. **Direct Commands**:
                - When the user directly asks for something (e.g., "create a file", "make a file"), 
                use the command syntax **without** the `#` prefix. Example:
                    ```
                    <<< create_file
                    ///path
                    example.txt
                    ///content
                    This is the file content.
                    >>>
                    ```
                
            2. **Example Commands**:
                - When the user asks for an **example** of how to use a command (e.g., "how would you create a file?"), 
                use the `#` prefix to indicate it is an example. Example:
                    ```
                    #<<< create_file
                    #///path
                    #example.txt
                    #///content
                    #This is an example file content.
                    #>>>
                    ```
            
            Note that below, you'll have only the "direct commands" listed, but if you are making an example, 
            you can use the example syntax.
            
            In case the interface has a bug and you are not able to navigate, you can use an escape code "SHUT_DOWN_DEEP_RESEARCHER". 
            If the system detects this code anywhere in your response it will halt the system and the admin will check it.
            """
            )
        )

        self._add_help_content(
            textwrap.dedent(f"""
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
            When you send a message without completing the task, you'll be able to continue with sending your next message, 
            the turn will not move to the user.
            If the task requires information that you don't yet have, or want to check something, you can use the commands, 
            finish your message, 
            the engine will run the commands and you'll see the results, which will allow you to continue with the task in next messages.

            Then after you have confirmed that you finished the task, and you want to show your results to the user, you can use 
            the done command.
            
            You should aim to minimize user interventions until you achieve your task.
            But if it is the case that you lack some important information, don't make assumptions.
            Compile clear, good questions, then use the ask_the_user command to get that information from the user.
            The user will be informed about your command, but preferrably run it early in the process, while they are at the computer.
            
            *Don't see response of command you are executed?*
            You won't receive the response of the commands you use immediately. You need to finish your message, without having the 
            response, to allow the engine to run your commands.
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
            
            ### Commands FAQ
            
            #### Q: What to do if I don't see any results
            
            A: If you send a command, a search, and don't see any results, that's likely because you didn't finish your message to wait for 
            the engine to process the whole message. Just finish your message and wait.
            The concept of sending a full message for processing and receiving a consolidated response requires a shift from interactive 
            interfaces but allows for batch processing of commands
            
            #### Q: How many commands to send at once?
            
            A: If you already know that you'll need multiple pieces of information, and getting the results of part of them won't influence 
            the need for others, send a command for all of them, don't spend another message/response cycle. Commands are parallelizable! 
            You can go even with 20-30 commands without worry, you'll then receive all of their outputs in the response.
            
            #### Q: How to input same argument multiple times for a command?
            
            A: You need to put `///section_name` each time, example:
            <<< command_with_multiple_inputs
            ///title
            title 1
            ///title
            title 2
            >>>
            
            #### Q: When to finish problem?
            
            A: You should always verify the results (not details, but the completeness) before finishing the task.
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

            additional_information = command.get_additional_information()

            is_agent_command = additional_information.get("is_agent_only")

            if command_status_override == "OFF":
                is_enabled = False
            elif command_status_override == "ON":
                is_enabled = True
            elif command_status_override == "AGENT_ONLY":
                is_enabled = self._agent_mode
            else:
                if not is_agent_command or self._agent_mode:
                    is_enabled = True

            if is_enabled:
                content.append(self._render_command_help(name, command))

        return "\n".join(content)

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
        from hermes.interface.commands.help_generator import CommandHelpGenerator

        help_generator = CommandHelpGenerator()
        return help_generator.generate_help({name: command})
