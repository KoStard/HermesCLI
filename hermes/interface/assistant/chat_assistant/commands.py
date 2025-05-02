import logging
import os
from typing import Any, Dict, Generator

from hermes.event import (
    AssistantDoneEvent,
    Event,
    FileEditEvent,
    MessageEvent,
)
from hermes.interface.commands import Command
from hermes.interface.helpers import CLIColors
from hermes.message import (
    LLMRunCommandOutput,
    TextMessage,
    TextualFileMessage,
    UrlMessage,
)
from hermes.utils.file_extension import remove_quotes
from hermes.utils.filepath import prepare_filepath
from hermes.utils.tree_generator import TreeGenerator

logger = logging.getLogger(__name__)


class ChatAssistantCommandContext:
    """Context for executing ChatAssistant commands."""

    def __init__(self, control_panel):
        self.control_panel = control_panel
        self.notifications_printer = control_panel.notifications_printer
        self.exa_client = control_panel.exa_client
        self._cwd = os.getcwd()

    def print_notification(self, message: str, color: CLIColors = CLIColors.BLUE) -> None:
        """Print a notification using the notifications printer."""
        self.notifications_printer.print_notification(message, color)

    def get_cwd(self) -> str:
        """Get the current working directory."""
        return self._cwd


class CreateFileCommand(Command[ChatAssistantCommandContext]):
    """Create a new file with provided content."""

    def __init__(self):
        super().__init__(
            "create_file", 
            """Create a new file with the specified content.

**IMPORTANT:** When the user asks you to "create a file", "make a file", "generate a file", or uses similar wording that implies the creation of a new file, you **MUST** use this command.

The content will be written to the file as-is, without any additional formatting.

Make sure not to override anything important from the OS, to avoid causing frustration and losing trust with the user.
The user will be asked to confirm or reject if you are overwriting an existing file.

If the user hasn't mentioned where to create a file, or you just want to create a sandbox file, create it in /tmp/hermes_sandbox/ folder.

If any of the folders in the filepath don't exist, the folders will be automatically created."""
        )
        self.add_section("path", True, "Path to the file to create (relative or absolute)")
        self.add_section("content", True, "Content to write to the file")

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        file_path = prepare_filepath(remove_quotes(args["path"]))
        content = args["content"]

        context.print_notification(f"Creating file: {file_path}")
        yield FileEditEvent(file_path=file_path, content=content, mode="create")


class AppendFileCommand(Command[ChatAssistantCommandContext]):
    """Append content to an existing file."""

    def __init__(self):
        super().__init__(
            "append_file", 
            """Append content to the end of an existing file or create it if it doesn't exist.

The content will be appended as-is to the end of the file, without any additional formatting.
If the file doesn't exist yet, it will be created."""
        )
        self.add_section("path", True, "Path to the file to append to (relative or absolute)")
        self.add_section("content", True, "Content to append to the file")

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        file_path = prepare_filepath(remove_quotes(args["path"]))
        content = args["content"]

        context.print_notification(f"Appending to file: {file_path}")
        yield FileEditEvent(file_path=file_path, content=content, mode="append")


class PrependFileCommand(Command[ChatAssistantCommandContext]):
    """Add content to the beginning of a file."""

    def __init__(self):
        super().__init__(
            "prepend_file", 
            """Add content to the beginning of a file.

The content will be inserted at the top of the file as-is, without any additional formatting.
If the file doesn't exist yet, it will be created."""
        )
        self.add_section("path", True, "Path to the file to prepend to (relative or absolute)")
        self.add_section("content", True, "Content to add to the beginning of the file")

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        file_path = prepare_filepath(remove_quotes(args["path"]))
        content = args["content"]

        context.print_notification(f"Prepending to file: {file_path}")
        yield FileEditEvent(file_path=file_path, content=content, mode="prepend")


class MarkdownUpdateSectionCommand(Command[ChatAssistantCommandContext]):
    """Replace content in a markdown section."""

    def __init__(self):
        super().__init__(
            "markdown_update_section", 
            """Replace content in a specific section of a markdown file.

How the section path works:
1. You point at the section with the section path. The section path doesn't say what happens with the content.
2. The section path includes everything in its scope. Except for __preface, it also includes all the children (sections with higher level)
3. You specify the section path by writing the section titles (without the #) separated by '>'. Example: T1 > T2 > T3
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

The section path must exactly match the headers in the document.
Sections are identified by their markdown headers (##, ###, etc).
This command doesn't work on non-markdown files.

Examples:
<<< markdown_update_section
///path
path/to/My document.md
///section_path
Introduction > Overview
///content
This is some for the Overview section under Introduction.
Some more content here.
>>>
"""
        )
        self.add_section("path", True, "Path to the markdown file")
        self.add_section("section_path", True, "Section path (e.g., 'Header 1 > Subheader')")
        self.add_section("content", True, "New content for the section")

    def transform_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        if "path" in args and "section_path" in args:
            # The section_path is currently parsed as a single string, but needs to be a list
            section_path_raw = args["section_path"]
            section_path = [s.strip() for s in section_path_raw.split(">")]
            args["section_path"] = section_path
            
            # Ensure file path is properly prepared
            args["path"] = prepare_filepath(remove_quotes(args["path"].strip()))
        return args

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        file_path = args["path"]
        section_path = args["section_path"]
        content = args["content"]

        context.print_notification(f"Updating markdown section in: {file_path}")
        yield FileEditEvent(
            file_path=file_path,
            content=content,
            mode="update_markdown_section",
            submode="update_markdown_section",
            section_path=section_path
        )


class MarkdownAppendSectionCommand(Command[ChatAssistantCommandContext]):
    """Append content to a markdown section."""

    def __init__(self):
        super().__init__(
            "markdown_append_section", 
            """Append content to a specific section in a markdown file.

It works the same as `markdown_update_section`, but the content will be appended to the section instead of replacing it.
If the selected section contains child sections, the content will be appended at the end of the whole section, including the child sections.
Example:
    Document content:
    ## Chapter 1
    ### Section 1.1
    ### Section 1.2
    
    Using this command:
    <<< markdown_append_section
    ///path
    document.md
    ///section_path
    Chapter 1
    ///content
    This content will be appended to the end of Chapter 1.
    >>>

    This will produce:
    ## Chapter 1
    ### Section 1.1
    ### Section 1.2
    This content will be appended to the end of Chapter 1.
    
This command doesn't work on non-markdown files."""
        )
        self.add_section("path", True, "Path to the markdown file")
        self.add_section("section_path", True, "Section path (e.g., 'Header 1 > Subheader')")
        self.add_section("content", True, "Content to append to the section")

    def transform_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        if "path" in args and "section_path" in args:
            # The section_path is currently parsed as a single string, but needs to be a list
            section_path_raw = args["section_path"]
            section_path = [s.strip() for s in section_path_raw.split(">")]
            args["section_path"] = section_path
            
            # Ensure file path is properly prepared
            args["path"] = prepare_filepath(remove_quotes(args["path"].strip()))
        return args

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        file_path = args["path"]
        section_path = args["section_path"]
        content = args["content"]

        context.print_notification(f"Appending to markdown section in: {file_path}")
        yield FileEditEvent(
            file_path=file_path,
            content=content,
            mode="update_markdown_section",
            submode="append_markdown_section",
            section_path=section_path
        )


class TreeCommand(Command[ChatAssistantCommandContext]):
    """Generate a directory tree structure."""

    def __init__(self):
        super().__init__(
            "tree", 
            """Generate a directory tree structure.

This command shows the structure of files and directories starting from the given path.
You can optionally specify a maximum depth to limit how deep the tree will go.

If no path is provided, the current working directory will be used.
If no depth is specified, the complete tree will be generated."""
        )
        self.add_section("path", False, "Directory path to generate tree for (default: current directory)")
        self.add_section("depth", False, "Maximum depth of the tree (default: full depth)")

    def transform_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        # Set default values if not provided
        if "path" not in args or not args["path"].strip():
            args["path"] = os.getcwd()
        else:
            args["path"] = remove_quotes(args["path"].strip())

        if "depth" in args and args["depth"].strip():
            try:
                args["depth"] = int(args["depth"].strip())
            except ValueError:
                args["depth"] = None
        else:
            args["depth"] = None
            
        return args

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        path = args["path"]
        depth = args["depth"]

        try:
            tree_generator = TreeGenerator()
            tree_string = tree_generator.generate_tree(path, depth)
            yield MessageEvent(LLMRunCommandOutput(text=tree_string, name="Directory Tree"))
        except Exception as e:
            error_msg = f"Error generating tree for {path}: {str(e)}"
            context.print_notification(error_msg, CLIColors.RED)
            yield MessageEvent(LLMRunCommandOutput(text=error_msg, name="Directory Tree Error"))


class OpenFileCommand(Command[ChatAssistantCommandContext]):
    """Read and return the contents of a file."""

    def __init__(self):
        super().__init__(
            "open_file", 
            """Read and return the contents of a file.

This command allows you to read the content of any file that the user has access to.
The file content will be returned as a message that you can analyze in your next response.

If the file doesn't exist or cannot be read due to permissions, an error message will be shown."""
        )
        self.add_section("path", True, "Path to the file to read (relative or absolute)")

    def transform_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        if "path" in args:
            args["path"] = prepare_filepath(remove_quotes(args["path"].strip()))
        return args

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        file_path = args["path"]
        
        if not os.path.exists(file_path):
            error_msg = f"Error: File not found at {file_path}"
            context.print_notification(error_msg, CLIColors.RED)
            yield MessageEvent(LLMRunCommandOutput(text=error_msg, name="File Error"))
        elif not os.access(file_path, os.R_OK):
            error_msg = f"Error: Permission denied reading {file_path}"
            context.print_notification(error_msg, CLIColors.RED)
            yield MessageEvent(LLMRunCommandOutput(text=error_msg, name="File Error"))
        else:
            context.print_notification(f"Reading file: {file_path}")
            yield MessageEvent(
                TextualFileMessage(
                    author="user",
                    text_filepath=file_path,
                    textual_content=None,
                    file_role="CommandOutput",
                )
            )


class DoneCommand(Command[ChatAssistantCommandContext]):
    """Mark a task as done and provide a final report."""

    def __init__(self):
        super().__init__(
            "done", 
            """Mark the current task as done and provide a final report to the user.

You can take as many steps as you need to accomplish the task before running this command.
The report should summarize what you've done, any issues encountered, and the final results.

IMPORTANT: Only use this command when you have actually completed the task.
If you run this command without finishing the task, it will cause loss of user trust.
Make sure you have finished and read through all the command outputs before marking the task as done."""
        )
        self.add_section("report", True, "Final report summarizing what was accomplished")

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        report_content = args["report"]
        
        context.print_notification("Agent marked task as done")
        yield AssistantDoneEvent()
        yield MessageEvent(
            TextMessage(
                author="assistant",
                text=report_content,
                text_role="AgentReport",
                name="Task Completion Report",
            )
        )
    
    def get_additional_information(self):
        return {
            "is_agent_only": True
        }


class AskTheUserCommand(Command[ChatAssistantCommandContext]):
    """Ask the user for clarification or information."""

    def __init__(self):
        super().__init__(
            "ask_the_user", 
            """Ask the user for clarification or specific information needed to complete the task.

Use this when you need additional information from the user to proceed.
Be specific and clear about what information you need.
Try to compile multiple related questions into a single request to minimize user interventions.

Running this command will end your current turn and wait for the user's response."""
        )
        self.add_section("question", True, "Question(s) for the user - be specific about what you need")

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        question_content = args["question"]
        
        context.print_notification("Agent is asking the user a question")
        yield AssistantDoneEvent()
        yield MessageEvent(
            TextMessage(
                author="assistant",
                text=question_content,
                text_role="AgentQuestion",
                name="Task Related Question",
            )
        )
    
    def get_additional_information(self):
        return {
            "is_agent_only": True
        }


class WebSearchCommand(Command[ChatAssistantCommandContext]):
    """Perform a web search using Exa API."""

    def __init__(self):
        super().__init__(
            "web_search", 
            """Perform a web search using the Exa API.

This command returns up to 10 relevant results from the web based on your query.
Each result includes the title, URL, and when available, author and publication date.

IMPORTANT: This API costs the user money. Only use this command when directly asked to do a web search,
or when you absolutely need up-to-date information that isn't in your knowledge cutoff."""
        )
        self.add_section("query", True, "Search query - be specific for better results")

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        query = args["query"]

        if not context.exa_client:
            error_msg = "Error: Exa client not configured"
            context.print_notification(error_msg, CLIColors.RED)
            yield MessageEvent(LLMRunCommandOutput(text=error_msg, name="Web Search Error"))
            return

        try:
            results = context.exa_client.search(query, num_results=10)

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
                TextualFileMessage(
                    author="assistant",
                    text_filepath=None,
                    textual_content="\n".join(result_text),
                    file_role="WebSearchResults",
                    name=f"Web Search: {query}",
                )
            )

        except Exception as e:
            error_msg = f"Error performing web search: {str(e)}"
            context.print_notification(error_msg, CLIColors.RED)
            yield MessageEvent(LLMRunCommandOutput(text=error_msg, name="Web Search Error"))
    
    def get_additional_information(self):
        return {
            "is_agent_only": True
        }


class OpenUrlCommand(Command[ChatAssistantCommandContext]):
    """Read and return the contents of a URL."""

    def __init__(self):
        super().__init__(
            "open_url", 
            """Read and return the contents of a URL.

This command fetches content from the specified URL and returns it for your analysis.
Use this after a web search to read specific pages, or when the user provides you with a URL.

If Exa API is configured, it will be used to get enhanced content."""
        )
        self.add_section("url", True, "URL to fetch content from (must be a valid, complete URL)")

    def execute(self, context: ChatAssistantCommandContext, args: Dict[str, Any]) -> Generator[Event, None, None]:
        url = args["url"].strip()
        
        if not url:
            error_msg = "Error: No URL provided"
            context.print_notification(error_msg, CLIColors.RED)
            yield MessageEvent(LLMRunCommandOutput(text=error_msg, name="URL Error"))
            return

        context.print_notification(f"Opening URL: {url}")
        yield MessageEvent(UrlMessage(author="user", url=url))
    
    def get_additional_information(self):
        return {
            "is_agent_only": True
        }
