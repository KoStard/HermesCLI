import os
from collections.abc import Generator
from typing import Any

from hermes.chat.events import Event
from hermes.chat.interface.assistant.chat_assistant.commands.context import (
    ChatAssistantCommandContext,
    ChatAssistantExecuteResponseType,
)
from hermes.chat.interface.commands.command import Command
from hermes.chat.interface.helpers.cli_notifications import CLIColors # Specifically used in context.confirm_file_overwrite_with_user
from hermes.utils.file_extension import remove_quotes
from hermes.utils.filepath import prepare_filepath


class CreateFileCommand(Command[ChatAssistantCommandContext, ChatAssistantExecuteResponseType]):
    """Create a new file with provided content."""

    def __init__(self):
        super().__init__(
            "create_file",
            """Create a new file with the specified content.

**IMPORTANT:** When the user asks you to "create a file", "make a file", "generate a file",
or uses similar wording that implies the creation of a new file, you **MUST** use this command.

The content will be written to the file as-is, without any additional formatting.

Make sure not to override anything important from the OS, to avoid causing frustration and losing trust with the user.
The user will be asked to confirm or reject if you are overwriting an existing file.

If the user hasn't mentioned where to create a file, or you just want to create a sandbox file, create it in /tmp/hermes_sandbox/ folder.

If any of the folders in the filepath don't exist, the folders will be automatically created.""",
        )
        self.add_section("path", True, "Path to the file to create (relative or absolute)")
        self.add_section("content", True, "Content to write to the file")

    def execute(self, context: ChatAssistantCommandContext, args: dict[str, Any]) -> Generator[Event, None, None]:
        file_path = prepare_filepath(remove_quotes(args["path"]))
        content = args["content"]

        if os.path.exists(file_path):
            if not context.confirm_file_overwrite_with_user(file_path):
                yield context.create_assistant_notification(
                    f"File creation aborted: File with same path existed and user declined to overwrite {file_path}",
                    "File Creation Cancelled",
                )
                return

            yield context.create_assistant_notification(
                f"File {file_path} already exists. Creating backup before overwriting.",
                "File Creation",
            )

        context.print_notification(f"Creating file: {file_path}")
        success = context.create_file(file_path, content)

        if success:
            yield context.create_assistant_notification(f"Successfully created file: {file_path}", "File Creation")
        else:
            yield context.create_assistant_notification(f"Failed to create file: {file_path}", "File Creation Error")
