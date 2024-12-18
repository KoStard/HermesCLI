import logging
import os
import textwrap
from typing import Generator

from hermes.utils.file_extension import remove_quotes
from .base_control_panel import ControlPanel, ControlPanelCommand
from .peekable_generator import PeekableGenerator, iterate_while
from hermes.message import Message, TextGeneratorMessage, TextMessage
from hermes.event import FileEditEvent, Event, MessageEvent

logger = logging.getLogger(__name__)

class LLMControlPanel(ControlPanel):
    def __init__(self, extra_commands: list[ControlPanelCommand] = None):
        super().__init__()

        self._add_help_content("You are allowed to use the following commands. Use them **only** if the user directly asks for them. Understand that they can cause the user frustration and lose trust if used incorrectly. The commands will be programmatically parsed, make sure to follow the instructions precisely when using them. You don't have access to tools other than these. If the content doesn't match these instructions, they will be ignored. The command syntax should be used literally, symbol-by-symbol correctly.")
        
        self._register_command(ControlPanelCommand(
            command_label="///create_file",
            command_key="create_file",
            description=textwrap.dedent(
            f"""
            **IMPORTANT:** When the user asks you to "create a file", "make a file", "generate a file", or uses similar wording that implies the creation of a new file, you **MUST** use the `///create_file` command.
            Create a new file. Syntax: `///create_file <relative_or_absolute_file_path>`, from next line write the file content, finish with `///end_file` in a new line. 
            Everything between the opening and closing tags should be the valid content of the desired file, nothing else is allowed.
            The content will go to the file as-is, without any additional formatting.
            Example (don't put ``` even for code):
            ///create_file experiment.py
            import random
            print(random.randint(0, 100))
            ///end_file
            
            Another example for same content, but relative path:
            
            ///create_file ../experiments/experiment.py
            import random
            print(random.randint(0, 100))
            ///end_file
            
            ///create_file ~/Downloads/experiment.py
            import random
            print(random.randint(0, 100))
            ///end_file
            
            Make sure not to override anything important from the OS, not to cause frustration and lose trust with the customer.
            The user will be asked to confirm or reject if you are overwriting an existing file.

            If the user hasn't mentioned where to create a file, or you just want to create a sandbox file, create it in /tmp/hermes_sandbox/ folder.
            
            **CURRENT WORKING DIRECTORY:** {os.getcwd()}
            All relative paths will be resolved from this location.
            """),
            parser=lambda line, peekable_generator: FileEditCommandHandler(line, "create").handle(peekable_generator)
        ))
        
        self._register_command(ControlPanelCommand(
            command_label="///append_file",
            command_key="append_file",
            description=textwrap.dedent(
            f"""
            Append content to an existing file or create if it doesn't exist. Syntax: `///append_file <relative_or_absolute_file_path>`, from next line write the content to append, finish with `///end_file` in a new line.
            Everything between the opening and closing tags will be appended to the file, nothing else is allowed.
            The content will be appended as-is, without any additional formatting.
            Example (don't put ``` even for code):
            ///append_file experiment.py
            # Adding more content
            print("This will be appended")
            ///end_file
            
            **CURRENT WORKING DIRECTORY:** {os.getcwd()}
            All relative paths will be resolved from this location.
            """),
            parser=lambda line, peekable_generator: FileEditCommandHandler(line, "append").handle(peekable_generator)
        ))

        if extra_commands:
            for command in extra_commands:
                self._register_command(command)

    def render(self) -> str:
        content = []
        content.append(self._render_help_content())
        for command_label in self.commands:
            content.append(self._render_command_in_control_panel(command_label))
        return "\n".join(content)

    def break_down_and_execute_message(self, message: Message) -> Generator[Event, None, None]:
        peekable_generator = PeekableGenerator(self._lines_from_message(message))

        while True:
            try:
                line = peekable_generator.peek()
            except StopIteration:
                return

            command_label = self._line_command_match(line)

            if command_label:
                next(peekable_generator) # Consume the line

                yield from self.commands[command_label].parser(line, peekable_generator)
            else:
                yield MessageEvent(TextGeneratorMessage(author="assistant", text_generator=iterate_while(peekable_generator, lambda line: not self._line_command_match(line)), is_directory_entered=True)) 

class FileEditCommandHandler:
    def __init__(self, line: str, mode: str):
        """
        Possible inputs of line. It can contain only one value. Allow spaces in the names.
        filename.extension
        ./relative/path/filename.extension
        ../../relative/path/filename.extension
        /absolute/path/filename.extension
        ~/absolute/path/filename.extension
        """
        self.line = line
        self.mode = mode
        # The line contains the command, so it starts with `///create_file ` or `///append_file `
        raw_path = line.split(" ", 1)[1].strip()
        unquoted_path = remove_quotes(raw_path)
        self.file_path = self._escape_filepath(unquoted_path)

        self._content = []

    def handle(self, peekable_generator: PeekableGenerator) -> Generator[Event, None, None]:
        # TODO: The AI should be asked to repeat if the structure is invalid.
        for line in peekable_generator:
            if line.strip() == "///end_file":
                yield self._finish()
                return
            else:
                print(line, end="")
                self._content.append(line)
        if self._content:
            yield self._finish()

    def _finish(self):
        file_edit_event = FileEditEvent(file_path=self.file_path, content="".join(self._content), mode=self.mode)
        self._content = []
        return file_edit_event

    def _escape_filepath(self, filepath_expression: str) -> str:
        """
        Convert various filepath formats to a normalized absolute path.
        
        Args:
            filepath_expression: Input path that can be:
                - filename.extension
                - ./relative/path/filename.extension
                - ../../relative/path/filename.extension
                - /absolute/path/filename.extension
                - ~/absolute/path/filename.extension
                
        Returns:
            Normalized absolute path
        """
        # Expand user directory (~)
        expanded_path = os.path.expanduser(filepath_expression)
        
        # Convert to absolute path if relative
        if not os.path.isabs(expanded_path):
            expanded_path = os.path.abspath(expanded_path)
            
        # Normalize the path (resolve .. and . components)
        normalized_path = os.path.normpath(expanded_path)
        
        return normalized_path
