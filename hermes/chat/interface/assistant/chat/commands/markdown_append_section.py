from collections.abc import Generator
from typing import Any

from hermes.chat.events import Event
from hermes.chat.interface.assistant.chat.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.utils.file_extension import remove_quotes
from hermes.utils.filepath import prepare_filepath


class MarkdownAppendSectionCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
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

This command doesn't work on non-markdown files.""",
        )
        self.add_section("path", True, "Path to the markdown file")
        self.add_section("section_path", True, "Section path (e.g., 'Header 1 > Subheader')")
        self.add_section("content", True, "Content to append to the section")

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        if "path" in args and "section_path" in args:
            section_path_raw = args["section_path"]
            section_path = [s.strip() for s in section_path_raw.split(">")]
            args["section_path"] = section_path
            args["path"] = prepare_filepath(remove_quotes(args["path"].strip()))
        return args

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        file_path = args["path"]
        section_path = args["section_path"]
        content = args["content"]

        context.print_notification(f"Appending to markdown section in: {file_path}")
        success = context.update_markdown_section(
            file_path=file_path,
            section_path=section_path,
            new_content=content,
            submode="append_markdown_section",
        )

        action_name = "appended to"
        if success:
            yield context.create_assistant_notification(
                f"Successfully {action_name} markdown section '{' > '.join(section_path)}' in {file_path}",
                "Markdown Append",
            )
        else:
            yield context.create_assistant_notification(
                f"Failed to {action_name} markdown section '{' > '.join(section_path)}' in {file_path}",
                "Markdown Append Error",
            )
