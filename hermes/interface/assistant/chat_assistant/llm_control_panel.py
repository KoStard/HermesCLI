import logging
import os
import textwrap
from typing import Generator
from hermes.interface.helpers.cli_notifications import CLINotificationsPrinter
from hermes.interface.helpers.terminal_coloring import CLIColors
from hermes.utils.filepath import prepare_filepath
from hermes.utils.file_extension import remove_quotes
from hermes.utils.tree_generator import TreeGenerator
from hermes.interface.control_panel.base_control_panel import (
    ControlPanel,
    ControlPanelCommand,
)
from hermes.interface.helpers.peekable_generator import PeekableGenerator, iterate_while
from hermes.message import (
    LLMRunCommandOutput,
    Message,
    TextGeneratorMessage,
    TextMessage,
    TextualFileMessage,
    UrlMessage,
)
from hermes.event import AssistantDoneEvent, FileEditEvent, Event, MessageEvent

logger = logging.getLogger(__name__)


class LLMControlPanel(ControlPanel):
    def __init__(
        self,
        notifications_printer: CLINotificationsPrinter,
        extra_commands: list[ControlPanelCommand] = None,
        exa_client=None,
        command_status_overrides: dict = None,
    ):
        super().__init__()
        self.notifications_printer = notifications_printer
        self.exa_client = exa_client
        self._agent_mode = False
        self._commands_parsing_status = True

        # Add help content
        self._add_initial_help_content()

        # Register core file editing commands
        self._register_file_commands()

        # Register markdown section commands
        self._register_markdown_commands()

        # Register utility commands
        self._register_utility_commands()

        # Register agent-only commands
        self._register_agent_commands()

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
            
            1. **Direct Commands**:
                - When the user directly asks for a file to be created (e.g., "create a file", "make a file"), use the command syntax **without** the `#` prefix. Example:
                    ```
                    ///create_file example.txt
                    This is the file content.
                    ///end_file
                    ```
                
            2. **Example Commands**:
                - When the user asks for an **example** of how to use a command (e.g., "how would you create a file?"), use the `#` prefix to indicate it is an example. Example:
                    ```
                    #///create_file example.txt
                    This is an example file content.
                    #///end_file
                    ```
            
            Note that below, you'll have only the "direct commands" listed, but if you are making an example, you can use the example syntax.
            
            **Getting the output of the commands**
            You'll see the results of the command after you send your final message.
            """
            )
        )

        self._add_help_content(
            textwrap.dedent("""
        If you are specifying a filepath that has spaces, you should enclose the path in double quotes. For example:
        ///create_file "path with spaces/file.txt"
        
        While if you are specifying a filepath that doesn't have spaces, you can skip the quotes. For example:
        ///create_file path_without_spaces/file.txt
        """)
        )

    def _register_file_commands(self):
        """Register commands for file creation and editing"""
        self._register_command(
            ControlPanelCommand(
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
            """
                ),
                parser=lambda line, peekable_generator: FileEditCommandHandler(
                    line, "create"
                ).handle(peekable_generator),
            )
        )

        self._register_command(
            ControlPanelCommand(
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
            """
                ),
                parser=lambda line, peekable_generator: FileEditCommandHandler(
                    line, "append"
                ).handle(peekable_generator),
            )
        )

        self._register_command(
            ControlPanelCommand(
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
            """
                ),
                parser=lambda line, peekable_generator: FileEditCommandHandler(
                    line, "prepend"
                ).handle(peekable_generator),
            )
        )

    def _register_markdown_commands(self):
        """Register commands for markdown section editing"""
        self._register_command(
            ControlPanelCommand(
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
            """
                ),
                parser=lambda line, peekable_generator: MarkdownSectionCommandHandler(
                    line, "update_markdown_section"
                ).handle(peekable_generator),
            )
        )

        self._register_command(
            ControlPanelCommand(
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
            """
                ),
                parser=lambda line, peekable_generator: MarkdownSectionCommandHandler(
                    line, "append_markdown_section"
                ).handle(peekable_generator),
            )
        )

    def _register_utility_commands(self):
        """Register utility commands for file and directory operations"""
        self._register_command(
            ControlPanelCommand(
                command_id="tree",
                command_label="///tree",
                short_description="Generate directory tree",
                description=textwrap.dedent(
                    f"""
            Generate a directory tree structure. Syntax: `///tree [<path>] [<depth>]`
            - path: Optional path to generate tree for (default: current directory)
              Use quotes around paths containing spaces: `///tree "path/with spaces"`
            - depth: Optional maximum depth of the tree (default: full depth)
            
            Examples:
            ///tree
            ///tree /path/to/dir
            ///tree /path/to/dir 2
            ///tree "path/with spaces"
            ///tree "path/with spaces" 2
            """
                ),
                parser=lambda line, peekable_generator: self._parse_tree_command(line),
            )
        )

        self._register_command(
            ControlPanelCommand(
                command_id="open_file",
                command_label="///open_file",
                short_description="Read file contents",
                description=textwrap.dedent(
                    f"""
            Read and return the contents of a file. Syntax: `///open_file <file_path>`
            - file_path: Path to the file to read (relative or absolute)
              Use quotes around paths containing spaces: `///open_file "path/with spaces/file.txt"`
            
            Examples:
            ///open_file example.txt
            ///open_file /path/to/file.txt
            ///open_file "path/with spaces/file.txt"
            
            **CURRENT WORKING DIRECTORY:** {os.getcwd()}
            All relative paths will be resolved from this location.
            """
                ),
                parser=lambda line, peekable_generator: self._parse_open_file_command(
                    line
                ),
            )
        )

    def _register_agent_commands(self):
        """Register commands that are only available in agent mode"""
        self._add_help_content(
            textwrap.dedent(
                """
            **Agent Mode Enabled**
            You are now in the agent mode.
            
            The difference here is that you don't have to finish the task in one reply.
            If the task is too big, you can finish it with multiple messages.
            When you send a message without ///done command, you'll be able to continue with sending your next message, the turn will not move to the user.
            If the task requires information that you don't yet have, or want to check something, you can use the commands, finish your message, 
            the engine will run the commands and you'll see the results, which will allow you to continue with the task in next messages.

            Then after you have confirmed that you finished the task, and you want to show your results to the user, you can add the ///done command.
            
            Notice that some commands have closing tags. You have to close one command to be able to start another command. If you don't close the current command, a new command won't be started and the lines with the new command will be considered as part of argument of the current command. Make sure you close the commands.
            
            You should aim to minimize user interventions until you achieve your task.
            But if it is the case that you lack some important information, don't make assumptions.
            Compile clear, good questions, then use ///ask_the_user command to get that information from the user.
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

        self._register_command(
            ControlPanelCommand(
                command_id="done",
                command_label="///done",
                short_description="Mark task as done and provide final report",
                description=textwrap.dedent(
                    """
            Mark the current task as done and provide a final report to the user.
            You can take as many steps as you need to accomplish the task before running ///done.
            If you run ///done without actually finishing the task, it will cause loss of customer trust.
            Make sure you have finished and read through all the command outputs before marking the task as done.
            Syntax: `///done`, followed by the report content on subsequent lines,
            ending with `///end_report` on a new line.
            
            Example:
            ///done
            I have completed the task. Here are the results:
            - Created 3 new files
            - Updated 2 existing files
            - Verified all changes work as expected
            ///end_report
            """
                ),
                parser=lambda line, peekable_generator: self._parse_done_command(
                    peekable_generator
                ),
                is_agent_command=True,
            )
        )

        self._register_command(
            ControlPanelCommand(
                command_id="ask_the_user",
                command_label="///ask_the_user",
                short_description="Ask the user for clarification or information",
                description=textwrap.dedent(
                    """
            Ask the user for clarification or information needed to complete the task.
            Syntax: `///ask_the_user`, followed by your question on subsequent lines,
            ending with `///end_question` on a new line.
            
            Example:
            ///ask_the_user
            I need to know:
            - What is your preferred color scheme?
            - Should I use light or dark mode?
            ///end_question
            
            Use this when you need specific information from the user to proceed.
            """
                ),
                parser=lambda line,
                peekable_generator: self._parse_ask_the_user_command(
                    peekable_generator
                ),
                is_agent_command=True,
            )
        )

        self._register_command(
            ControlPanelCommand(
                command_id="web_search",
                command_label="///web_search",
                short_description="Perform a web search",
                description=textwrap.dedent(
                    """
            **Web Search Command**
            You can perform web searches using the Exa API with:
            ///web_search <query>
            This will return up to 10 relevant results from the web.
            Example:
            ///web_search latest AI research papers
            
            Perform a web search using Exa API. Syntax: `///web_search <query>`
            This API costs the user money, use it only when directly asked to do so.
            Returns up to 10 relevant results.
            
            Example:
            ///web_search latest AI research papers
            """
                ),
                parser=lambda line, peekable_generator: self._parse_web_search_command(
                    line
                ),
                is_agent_command=True,
            )
        )

        self._register_command(
            ControlPanelCommand(
                command_id="open_url",
                command_label="///open_url",
                short_description="Read URL contents",
                description=textwrap.dedent(
                    f"""
            Read and return the contents of a URL. Syntax: `///open_url <url>`
            - url: The URL to fetch content from
            - Uses Exa API to get enhanced content if configured
            
            Use after search, or if you were provided a specific URL by the user or in other attachments.
            
            Examples:
            ///open_url https://example.com
            """
                ),
                parser=lambda line, peekable_generator: self._parse_open_url_command(
                    line
                ),
                is_agent_command=True,
            )
        )

    def _parse_web_search_command(self, content: str) -> Generator[Event, None, None]:
        """
        Parse the ///web_search command and perform a web search.

        Args:
            content: The search query

        Returns:
            Generator yielding MessageEvent with search results
        """
        if not content.strip():
            yield MessageEvent(
                LLMRunCommandOutput(
                    text="Error: No search query provided", name="Web Search Error"
                )
            )
            return

        query = content.strip()
        try:
            if not hasattr(self, "exa_client"):
                yield MessageEvent(
                    LLMRunCommandOutput(
                        text="Error: Exa client not configured", name="Web Search Error"
                    )
                )
                return

            results = self.exa_client.search(query, num_results=10)

            if not results:
                yield MessageEvent(
                    LLMRunCommandOutput(
                        text=f"No results found for: {query}",
                        name=f"Web Search: {query}",
                    )
                )
                return

            result_text = [f"# Web Search Results for: {query}\n"]
            for i, result in enumerate(results, 1):
                result_text.append(f"Result {i}:")
                result_text.append(f"  Title: {result.title}")
                result_text.append(f"  URL: {result.url}")
                if result.author:
                    result_text.append(f"  Author: {result.author}")
                if result.published_date:
                    result_text.append(f"  Published: {result.published_date}")
                result_text.append("")

            yield MessageEvent(
                TextMessage(
                    author="assistant",
                    text="\n".join(result_text),
                    text_role="WebSearchResults",
                    name=f"Web Search: {query}",
                )
            )

        except Exception as e:
            yield MessageEvent(
                LLMRunCommandOutput(
                    text=f"Error performing web search: {str(e)}",
                    name="Web Search Error",
                )
            )

    def render(self) -> str:
        content = []
        content.append(self._render_help_content(is_agent_mode=self._agent_mode))

        for command_label in self.commands:
            command = self.commands[command_label]
            command_id = command.command_id
            command_status_override = self._command_status_overrides.get(command_id)

            # Determine if command should be enabled based on:
            # 1. Status override if present
            # 2. Agent mode requirements
            is_enabled = False

            if command_status_override == "OFF":
                is_enabled = False
            elif command_status_override == "ON":
                is_enabled = True
            elif command_status_override == "AGENT_ONLY":
                is_enabled = self._agent_mode
            else:
                if not command.is_agent_command:
                    is_enabled = True
                elif self._agent_mode:
                    is_enabled = True

            if is_enabled:
                content.append(self._render_command_in_control_panel(command_label))
        return "\n".join(content)

    def break_down_and_execute_message(
        self, message: Message
    ) -> Generator[Event, None, None]:
        peekable_generator = PeekableGenerator(self._lines_from_message(message))

        if not self._commands_parsing_status:
            yield MessageEvent(
                TextGeneratorMessage(
                    author="assistant",
                    text_generator=peekable_generator,
                    is_directly_entered=True,
                )
            )
            return

        while True:
            try:
                full_line = peekable_generator.peek()
            except StopIteration:
                return

            command_label = self._line_command_match(full_line)

            if command_label:
                next(peekable_generator)  # Consume the line

                content = self._extract_command_content_in_line(
                    command_label, full_line
                )
                self.notifications_printer.print_notification(
                    f"LLM used command: {command_label}"
                )
                yield from self.commands[command_label].parser(
                    content, peekable_generator
                )
            else:
                # TODO, it's a problem, if the TextGeneratorMessage is not finished, and this method is called again for a yield.
                # Maybe we shouldn't have the text generator message andjust generate text messages.
                # We need a kind of lock otherwise.
                yield MessageEvent(
                    TextGeneratorMessage(
                        author="assistant",
                        text_generator=iterate_while(
                            peekable_generator,
                            lambda line: not self._line_command_match(line),
                        ),
                        is_directly_entered=True,
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

        if command_id not in [cmd.command_id for cmd in self.commands.values()]:
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

    def _parse_tree_command(self, content: str) -> Generator[Event, None, None]:
        """
        Parse the ///tree command and generate a directory tree.

        Args:
            content: The command content after the label

        Returns:
            Generator yielding MessageEvent with the tree structure
        """
        # Handle quoted paths with spaces
        import shlex

        parts = shlex.split(content)

        path = os.getcwd() if not parts else remove_quotes(parts[0])
        depth = int(parts[1]) if len(parts) > 1 else None

        tree_generator = TreeGenerator()
        tree_string = tree_generator.generate_tree(path, depth)
        tree_message = LLMRunCommandOutput(text=tree_string, name="Directory Tree")
        yield MessageEvent(tree_message)

    def _parse_done_command(
        self, peekable_generator: PeekableGenerator
    ) -> Generator[Event, None, None]:
        """
        Parse the ///done command and collect the report content.

        Args:
            peekable_generator: The generator of message lines

        Returns:
            Generator yielding MessageEvent with the final report
        """
        report_content = []
        for line in peekable_generator:
            if line.strip() == "///end_report":
                yield AssistantDoneEvent()
                yield MessageEvent(
                    TextMessage(
                        author="assistant",
                        text="\n".join(report_content),
                        text_role="AgentReport",
                        name="Task Completion Report",
                    )
                )
                return
            report_content.append(line)

        # If we reach here without finding ///end_report, yield what we have
        if report_content:
            yield AssistantDoneEvent()
            yield MessageEvent(LLMRunCommandOutput(text="\n".join(report_content)))

    def _parse_ask_the_user_command(
        self, peekable_generator: PeekableGenerator
    ) -> Generator[Event, None, None]:
        """
        Parse the ///ask_the_user command and collect the question content.

        Args:
            peekable_generator: The generator of message lines

        Returns:
            Generator yielding MessageEvent with the question
        """
        question_content = []
        for line in peekable_generator:
            if line.strip() == "///end_question":
                yield AssistantDoneEvent()
                yield MessageEvent(
                    TextMessage(
                        author="assistant",
                        text="\n".join(question_content),
                        text_role="AgentQuestion",
                        name="Task Related Question",
                    )
                )
                return
            question_content.append(line)

        # If we reach here without finding ///end_question, yield what we have
        if question_content:
            yield AssistantDoneEvent()
            yield MessageEvent(
                TextMessage(
                    author="assistant",
                    text="\n".join(question_content),
                    text_role="AgentQuestion",
                    name="Task Related Question",
                )
            )

    def _parse_open_url_command(self, content: str) -> Generator[Event, None, None]:
        """
        Parse the ///open_url command and fetch URL contents.

        Args:
            content: The command content after the label

        Returns:
            Generator yielding MessageEvent with URL contents
        """
        url = content.strip()
        if not url:
            yield MessageEvent(
                LLMRunCommandOutput(text="Error: No URL provided", name="URL Error")
            )
            return

        yield MessageEvent(UrlMessage(author="user", url=url))

    def _parse_open_file_command(self, content: str) -> Generator[Event, None, None]:
        """
        Parse the ///open_file command and return a TextualFileMessage.

        Args:
            content: The command content after the label

        Returns:
            Generator yielding MessageEvent with TextualFileMessage
        """
        import shlex

        parts = shlex.split(content)

        if not parts:
            yield MessageEvent(
                LLMRunCommandOutput(
                    text="Error: No file path provided", name="File Error"
                )
            )
            return

        file_path = remove_quotes(parts[0])
        normalized_path = prepare_filepath(file_path)

        if not os.path.exists(normalized_path):
            yield MessageEvent(
                LLMRunCommandOutput(
                    text=f"Error: File not found at {normalized_path}",
                    name="File Error",
                )
            )
        elif not os.access(normalized_path, os.R_OK):
            yield MessageEvent(
                LLMRunCommandOutput(
                    text=f"Error: Permission denied reading {normalized_path}",
                    name="File Error",
                )
            )
        else:
            yield MessageEvent(
                TextualFileMessage(
                    author="user",
                    text_filepath=normalized_path,
                    file_role="CommandOutput",
                )
            )

    def enable_agent_mode(self):
        self._agent_mode = True

    def disable_agent_mode(self):
        self._agent_mode = False
        # TODO: Inform the assistant that the agent mode was disabled and it might have lost access to some commands

    def set_commands_parsing_status(self, status):
        self._commands_parsing_status = status


class FileEditCommandHandler:
    def __init__(self, content: str, mode: str):
        """
        Possible inputs of content. It can contain only one value. Allow spaces in the names.
        filename.extension
        ./relative/path/filename.extension
        ../../relative/path/filename.extension
        /absolute/path/filename.extension
        ~/absolute/path/filename.extension
        """
        self.mode = mode
        # The content contains just the path after the command
        raw_path = content.strip()
        unquoted_path = remove_quotes(raw_path)
        self.file_path = prepare_filepath(unquoted_path)

        self._content = []

    def handle(
        self, peekable_generator: PeekableGenerator
    ) -> Generator[Event, None, None]:
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
        file_edit_event = FileEditEvent(
            file_path=self.file_path, content="".join(self._content), mode=self.mode
        )
        self._content = []
        return file_edit_event


class MarkdownSectionCommandHandler:
    def __init__(self, content: str, mode: str):
        """
        Parse the markdown update section command.
        Expected format: <file_path> <section1> > <section2> > ...
        """
        try:
            import shlex

            splitter = shlex.shlex(content, posix=True)
            splitter.quotes = '"'
            splitter.whitespace_split = True
            file_path, *rest = list(splitter)  # Split into [file_path, section_path]
            section_path_raw = " ".join(rest)
        except Exception as e:
            logger.warning(
                "shlex.split() failed, falling back to basic split, spaces won't work",
                e,
            )
            file_path, section_path_raw = content.split(
                " ", 1
            )  # Split into [file_path, section_path]

        self.file_path = prepare_filepath(remove_quotes(file_path.strip()))
        self.section_path = [s.strip() for s in section_path_raw.split(">")]
        self._content = []
        self.mode = mode

    def handle(
        self, peekable_generator: PeekableGenerator
    ) -> Generator[Event, None, None]:
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
            section_path=self.section_path,
        )
