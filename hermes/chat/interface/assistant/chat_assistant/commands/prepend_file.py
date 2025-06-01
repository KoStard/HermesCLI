import os
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


class PrependFileCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Add content to the beginning of a file."""

    def __init__(self):
        super().__init__(
            "prepend_file",
            """Add content to the beginning of a file.

The content will be inserted at the top of the file as-is, without any additional formatting.
If the file doesn't exist yet, it will be created.""",
        )
        self.add_section("path", True, "Path to the file to prepend to (relative or absolute)")
        self.add_section("content", True, "Content to add to the beginning of the file")

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        file_path = prepare_filepath(remove_quotes(args["path"]))
        content = args["content"]

        context.print_notification(f"Prepending to file: {file_path}")
        success = context.prepend_file(file_path, content)

        if success:
            yield context.create_assistant_notification(f"Successfully prepended to file: {file_path}", "File Prepend")
        else:
            yield context.create_assistant_notification(f"Failed to prepend to file: {file_path}", "File Prepend Error")
