import os
from collections.abc import Generator
from typing import Any

from hermes.chat.events.base import Event
from hermes.chat.events.message_event import MessageEvent
from hermes.chat.interface.assistant.chat.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.chat.interface.helpers.cli_notifications import CLIColors
from hermes.chat.messages import TextualFileMessage
from hermes.utils.file_extension import remove_quotes
from hermes.utils.filepath import prepare_filepath


class OpenFileCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Read and return the contents of a file."""

    def __init__(self):
        super().__init__(
            "open_file",
            """Read and return the contents of a file.

This command allows you to read the content of any file that the user has access to.
The file content will be returned as a message that you can analyze in your next response.

If the file doesn't exist or cannot be read due to permissions, an error message will be shown.""",
        )
        self.add_section("path", True, "Path to the file to read (relative or absolute)")

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        if "path" in args:
            args["path"] = prepare_filepath(remove_quotes(args["path"].strip()))
        return args

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        file_path = args["path"]

        if not os.path.exists(file_path):
            error_msg = f"Error: File not found at {file_path}"
            context.print_notification(error_msg, CLIColors.RED)
            yield context.create_assistant_notification(error_msg, "File Error")
        elif not os.access(file_path, os.R_OK):
            error_msg = f"Error: Permission denied reading {file_path}"
            context.print_notification(error_msg, CLIColors.RED)
            yield context.create_assistant_notification(error_msg, "File Error")
        else:
            context.print_notification(f"Reading file: {file_path}")
            try:
                yield MessageEvent(
                    TextualFileMessage(
                        author="user",
                        text_filepath=file_path,
                        textual_content=None,
                        file_role="CommandOutput",
                    ),
                )
                yield context.create_assistant_notification(f"Successfully read file: {file_path}", "File Read")
            except Exception as e:
                error_msg = f"Error reading file {file_path}: {str(e)}"
                context.print_notification(error_msg, CLIColors.RED)
                yield context.create_assistant_notification(error_msg, "File Error")
