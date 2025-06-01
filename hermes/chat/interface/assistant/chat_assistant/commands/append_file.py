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


class AppendFileCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Append content to an existing file."""

    def __init__(self):
        super().__init__(
            "append_file",
            """Append content to the end of an existing file or create it if it doesn't exist.

The content will be appended as-is to the end of the file, without any additional formatting.
If the file doesn't exist yet, it will be created.""",
        )
        self.add_section("path", True, "Path to the file to append to (relative or absolute)")
        self.add_section("content", True, "Content to append to the file")

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        file_path = prepare_filepath(remove_quotes(args["path"]))
        content = args["content"]

        context.print_notification(f"Appending to file: {file_path}")
        success = context.append_file(file_path, content)

        if success:
            yield context.create_assistant_notification(f"Successfully appended to file: {file_path}", "File Append")
        else:
            yield context.create_assistant_notification(f"Failed to append to file: {file_path}", "File Append Error")
