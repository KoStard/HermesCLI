from collections.abc import Generator
from typing import Any

from hermes.chat.events import Event
from hermes.chat.interface.assistant.chat_assistant.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.utils.file_extension import remove_quotes
from hermes.utils.filepath import prepare_filepath


class MarkdownUpdateSectionCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
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
5. The section path must start from the root node, which is the top-level header of the document. If there are multiple top-level headers,
include the one where the target section is.

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
""",
        )
        self.add_section("path", True, "Path to the markdown file")
        self.add_section("section_path", True, "Section path (e.g., 'Header 1 > Subheader')")
        self.add_section("content", True, "New content for the section")

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

        context.print_notification(f"Updating markdown section in: {file_path}")
        success = context.update_markdown_section(
            file_path=file_path,
            section_path=section_path,
            new_content=content,
            submode="update_markdown_section",
        )

        action_name = "updated"
        if success:
            yield context.create_assistant_notification(
                f"Successfully {action_name} markdown section '{' > '.join(section_path)}' in {file_path}",
                "Markdown Update",
            )
        else:
            yield context.create_assistant_notification(
                f"Failed to {action_name} markdown section '{' > '.join(section_path)}' in {file_path}",
                "Markdown Update Error",
            )
