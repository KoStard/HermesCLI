import logging
import os
import textwrap
from typing import Generator

from hermes.utils.file_extension import remove_quotes
from .base_control_panel import ControlPanel, ControlPanelCommand
from ..helpers.peekable_generator import PeekableGenerator, iterate_while
from hermes.message import Message, TextGeneratorMessage, TextMessage
from hermes.event import FileEditEvent, Event, MessageEvent

logger = logging.getLogger(__name__)

class LLMControlPanel(ControlPanel):
    def __init__(self, extra_commands: list[ControlPanelCommand] = None):
        super().__init__()

        self._add_help_content("You are allowed to use the following commands. Use them **only** if the user directly asks for them. Understand that they can cause the user frustration and lose trust if used incorrectly. The commands will be programmatically parsed, make sure to follow the instructions precisely when using them. You don't have access to tools other than these. If the content doesn't match these instructions, they will be ignored. The command syntax should be used literally, symbol-by-symbol correctly.")

        self._add_help_content(textwrap.dedent("""
        If you are specifying a filepath that has spaces, you should enclose the path in double quotes. For example:
        ///create_file "path with spaces/file.txt"
        
        While if you are specifying a filepath that doesn't have spaces, you can skip the quotes. For example:
        ///create_file path_without_spaces/file.txt
        """))
        
        self._register_command(ControlPanelCommand(
            command_id="create_file",
            command_label="///create_file",
            short_description="Create a new file",
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
            
            If any of the folders in the filepath don't exist, the folders will be automatically created.
            
            **CURRENT WORKING DIRECTORY:** {os.getcwd()}
            All relative paths will be resolved from this location.
            """),
            parser=lambda line, peekable_generator: FileEditCommandHandler(line, "create").handle(peekable_generator)
        ))

        
        # Register markdown section commands
        self._register_command(ControlPanelCommand(
            command_id="markdown_update_section",
            command_label="///markdown_update_section",
            short_description="Replace markdown section content",
            description=textwrap.dedent(
            f"""
            Update a specific section in a markdown file, doesn't work on non-markdown files. Syntax: `///markdown_update_section <file_path> <section_path>`, 
            where section_path is a '>' separated list of headers leading to the target section.

            More on the definition of the section path:
            1. You point at the section with the section path. The section path doesn't say what happens with the content.
            2. The section path includes everything in its scope. Except for __preface, it also includes all the children (sections with higher level)
            3. You specify the section path, by writing the section titles (without the #) separated by '>'. Example: T1 > T2 > T3
            4. It's possible you'll have content in the given parent section before the child section starts. To point at that content, 
                add '__preface' at the end of the section path. This will target the content inside that section, 
                before any other section starts (even child sections).
                Example:
                T1 > T2 > __preface
                to target:
                ## T1
                ### T2
                Some content <<< This content will be targeted
                #### T3
            5. The section path must start from the root node, which is the top-level header of the document. If there are multiple top-level headers, include the one where the target section is.
            
            From the next line you start the content that you want to update the section with, finish with `///end_section` in a new line.

            Examples:
            ///markdown_update_section document.md Introduction > Overview
            This is some for the Overview section under Introduction.
            ///end_section

            ///markdown_update_section document.md Chapter 1 > Section 1.1 > __preface
            This is some content inside Section 1.1. before any child sections (e.g. Section 1.1.1).
            ///end_section

            The section path must exactly match the headers in the document.
            Sections are identified by their markdown headers (##, ###, etc).
            """),
            parser=lambda line, peekable_generator: 
                MarkdownSectionCommandHandler(line, "update_markdown_section").handle(peekable_generator)
        ))

        self._register_command(ControlPanelCommand(
            command_id="markdown_append_section",
            command_label="///markdown_append_section",
            short_description="Add content to markdown section",
            description=textwrap.dedent(
            f"""
            Append content to a specific section in a markdown file, doesn't work on non-markdown files. Syntax: `///markdown_append_section <file_path> <section_path>`, 
            where section_path is a '>' separated list of headers leading to the target section.

            It works the same as `///markdown_update_section`, but the content will be appended to the section instead of replacing it.
            If the selected section contains child sections, the content will be appended in the end of the whole section, including the child sections.
            Example:
                Document content:
                ## Chapter 1
                ### Section 1.1
                ### Section 1.2
                ///markdown_append_section document.md Chapter 1
                This content will be appended to the end of Chapter 1.
                ///end_section

                This will produce this output:
                ## Chapter 1
                ### Section 1.1
                ### Section 1.2
                This content will be appended to the end of Chapter 1.
            """),
            parser=lambda line, peekable_generator: 
                MarkdownSectionCommandHandler(line, "append_markdown_section").handle(peekable_generator)
        ))
        self._register_command(ControlPanelCommand(
            command_id="append_file",
            command_label="///append_file",
            short_description="Append to file end",
            description=textwrap.dedent(
            f"""
            Append content to the end of an existing file or create if it doesn't exist. Syntax: `///append_file <relative_or_absolute_file_path>`, from next line write the content to append, finish with `///end_file` in a new line.
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

        self._register_command(ControlPanelCommand(
            command_id="prepend_file",
            command_label="///prepend_file",
            short_description="Add to file beginning",
            description=textwrap.dedent(
            f"""
            Same as ///append_file, but adding at the top of the file. Syntax: `///prepend_file <relative_or_absolute_file_path>`, from next line write the content to prepend, finish with `///end_file` in a new line.
            Example (don't put ``` even for code):
            ///prepend_file experiment.py
            # Adding content at the top
            print("This will be prepended")
            ///end_file
            
            **CURRENT WORKING DIRECTORY:** {os.getcwd()}
            All relative paths will be resolved from this location.
            """),
            parser=lambda line, peekable_generator: FileEditCommandHandler(line, "prepend").handle(peekable_generator)
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

                line = line.lstrip()
                yield from self.commands[command_label].parser(line, peekable_generator)
            else:
                yield MessageEvent(TextGeneratorMessage(author="assistant", text_generator=iterate_while(peekable_generator, lambda line: not self._line_command_match(line)), is_directly_entered=True)) 

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
        self.file_path = _escape_filepath(unquoted_path)

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

class MarkdownSectionCommandHandler:
    def __init__(self, line: str, mode: str):
        """
        Parse the markdown update section command.
        Expected format: ///markdown_update_section <file_path> <section1> > <section2> > ...
        """
        try:
            import shlex
            splitter = shlex.shlex(line, posix=True)
            splitter.quotes = '"'
            splitter.whitespace_split = True
            _, file_path, *rest = list(splitter)  # Split into [command, file_path, section_path]
            section_path_raw = " ".join(rest)
        except Exception as e:
            logger.warning("shlex.split() failed, falling back to basic s/append_fileplit, spaces won't work", e)
            _, file_path, section_path_raw = line.split(" ", 1)  # Split into [command, file_path, section_path]
            
        self.file_path = _escape_filepath(remove_quotes(file_path.strip()))
        self.section_path = [s.strip() for s in section_path_raw.split(">")]
        self._content = []
        self.mode = mode

    def handle(self, peekable_generator: PeekableGenerator) -> Generator[Event, None, None]:
        for line in peekable_generator:
            if line.strip() == "///end_section":
                yield self._finish()
                return
            else:
                print(line, end="")
                self._content.append(line)
        if self._content:
            yield self._finish()

    def _finish(self):
        return FileEditEvent(
            file_path=self.file_path,
            content="".join(self._content),
            mode="update_markdown_section",
            submode=self.mode,
            section_path=self.section_path
        )

def _escape_filepath(filepath_expression: str) -> str:
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
