import logging
import os
from typing import TYPE_CHECKING, Generator

from hermes.chat.events import MessageEvent
from hermes.chat.events.base import Event
from hermes.chat.interface.helpers.cli_notifications import CLIColors
from hermes.chat.messages import AssistantNotificationMessage

if TYPE_CHECKING:
    from hermes.chat.interface.user.control_panel.exa_client import ExaClient
    from hermes.chat.interface.helpers.cli_notifications import (
        CLINotificationsPrinter,
    )
    # from hermes.chat.interface.assistant.chat_assistant.control_panel import ChatAssistantControlPanel


logger = logging.getLogger(__name__)


ChatAssistantExecuteResponseType = Generator[Event, None, None]


class ChatAssistantCommandContext:
    """Context for executing ChatAssistant commands."""

    def __init__(self, control_panel):  # control_panel type is ChatAssistantControlPanel
        self.control_panel = control_panel
        self.notifications_printer: "CLINotificationsPrinter" = control_panel.notifications_printer
        self.exa_client: "ExaClient | None" = control_panel.exa_client
        self._cwd = os.getcwd()

    def print_notification(self, message: str, color: CLIColors = CLIColors.BLUE) -> None:
        """Print a notification using the notifications printer."""
        self.notifications_printer.print_notification(message, color)

    def get_cwd(self) -> str:
        """Get the current working directory."""
        return self._cwd

    def create_assistant_notification(self, message: str, name: str | None = None) -> MessageEvent:
        """Create a notification that's only visible to the assistant."""
        return MessageEvent(AssistantNotificationMessage(text=message, name=name))

    def ensure_directory_exists(self, file_path: str) -> None:
        """Create directory structure for the given file path if it doesn't exist."""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            self.print_notification(f"Creating directory structure: {directory}")
            os.makedirs(directory, exist_ok=True)

    def confirm_file_overwrite_with_user(self, file_path: str) -> bool:
        """Ask user for confirmation before overwriting an existing file.

        Args:
            file_path: The path to the file that would be overwritten

        Returns:
            bool: True if user confirms overwrite, False otherwise
        """
        if not os.path.exists(file_path):
            return True

        self.print_notification(f"File '{file_path}' already exists. Overwrite? (y/n): ")

        while True:
            try:
                response = input().strip().lower()
                if response in ["y", "yes"]:
                    return True
                elif response in ["n", "no"]:
                    self.print_notification(f"File overwrite declined for: {file_path}", CLIColors.YELLOW)
                    return False
                else:
                    self.print_notification("Please enter 'y' or 'n': ")
            except (KeyboardInterrupt, EOFError):
                self.print_notification("\nFile overwrite cancelled", CLIColors.YELLOW)
                return False

    def backup_existing_file(self, file_path: str) -> None:
        """Backup the existing file to prevent possible data loss."""
        if not os.path.exists(file_path):
            return
        import shutil
        from datetime import datetime

        backup_dir = os.path.join("/tmp", "hermes", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")
        shutil.copy2(file_path, backup_path)
        self.print_notification(f"Created backup at {backup_path}")

    def create_file(self, file_path: str, content: str) -> bool:
        """Create a file with the given content. If file exists, create a backup first."""
        try:
            if os.path.exists(file_path):
                self.backup_existing_file(file_path)
            self.ensure_directory_exists(file_path)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
            return True
        except Exception as e:
            self.print_notification(f"Error creating file {file_path}: {str(e)}", CLIColors.RED)
            return False

    def append_file(self, file_path: str, content: str) -> bool:
        """Append content to a file. Create if doesn't exist."""
        try:
            self.ensure_directory_exists(file_path)
            mode = "a" if os.path.exists(file_path) else "w"
            with open(file_path, mode, encoding="utf-8") as file:
                file.write(content)
            return True
        except Exception as e:
            self.print_notification(f"Error appending to file {file_path}: {str(e)}", CLIColors.RED)
            return False

    def prepend_file(self, file_path: str, content: str) -> bool:
        """Prepend content to a file. Create if doesn't exist."""
        try:
            self.ensure_directory_exists(file_path)
            if os.path.exists(file_path):
                with open(file_path, encoding="utf-8") as file:
                    existing_content = file.read()
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content + existing_content)
            else:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
            return True
        except Exception as e:
            self.print_notification(f"Error prepending to file {file_path}: {str(e)}", CLIColors.RED)
            return False

    def update_markdown_section(self, file_path: str, section_path: list[str], new_content: str, submode: str) -> bool:
        """Update a specific section in a markdown file."""
        try:
            from hermes.chat.interface.markdown.document_updater import (
                MarkdownDocumentUpdater,
            )
            self.ensure_directory_exists(file_path)
            updater = MarkdownDocumentUpdater(file_path)
            was_updated = updater.update_section(section_path, new_content, submode)
            if was_updated:
                return True
            else:
                self.print_notification(
                    f"Warning: Section {' > '.join(section_path)} not found in {file_path}. No changes made.",
                    color=CLIColors.YELLOW,
                )
                return False
        except Exception as e:
            self.print_notification(f"Error updating markdown section: {str(e)}", CLIColors.RED)
            return False
