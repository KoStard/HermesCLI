import os
import shutil
from datetime import datetime

from hermes.chat.interface.helpers.cli_notifications import CLIColors, CLINotificationsPrinter


class FileOperationsHandler:
    def __init__(self, notifications_printer: CLINotificationsPrinter):
        self.notifications_printer = notifications_printer

    def create_file(self, file_path: str, content: str) -> None:
        if not self._confirm_file_creation(file_path):
            return
        self._ensure_directory_exists(file_path)
        self._write_file_content(file_path, content)

    def append_to_file(self, file_path: str, content: str) -> None:
        self._ensure_directory_exists(file_path)
        self._append_content_to_file(file_path, content)

    def prepend_to_file(self, file_path: str, content: str) -> None:
        self._ensure_directory_exists(file_path)
        self._prepend_content_to_file(file_path, content)

    def update_markdown_section(self, file_path: str, section_path: list[str], content: str, submode: str) -> None:
        self._ensure_directory_exists(file_path)
        self._modify_markdown_section(file_path, section_path, content, submode)

    def _confirm_file_creation(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            self.notifications_printer.print_notification(f"File {file_path} already exists.")
            response = input("Do you want to overwrite it? [y/N] ").strip().lower()
            if response != "y":
                self.notifications_printer.print_notification("File creation cancelled.")
                return False
        return True

    def _create_backup(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            return

        backup_path = self._generate_backup_path(file_path)
        shutil.copy2(file_path, backup_path)
        self.notifications_printer.print_notification(f"Created backup at {backup_path}")

    def _generate_backup_path(self, file_path: str) -> str:
        backup_dir = os.path.join("/tmp", "hermes", "backups")
        os.makedirs(backup_dir, exist_ok=True)

        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(backup_dir, f"{filename}_{timestamp}.bak")

    def _ensure_directory_exists(self, file_path: str) -> None:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            self.notifications_printer.print_notification(f"Creating directory structure: {directory}")
            os.makedirs(directory, exist_ok=True)

    def _write_file_content(self, file_path: str, content: str) -> None:
        if os.path.exists(file_path):
            self._create_backup(file_path)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

    def _append_content_to_file(self, file_path: str, content: str) -> None:
        mode = "a" if os.path.exists(file_path) else "w"
        with open(file_path, mode, encoding="utf-8") as file:
            file.write(content)

    def _prepend_content_to_file(self, file_path: str, content: str) -> None:
        if os.path.exists(file_path):
            existing_content = self._read_file_content(file_path)
            self._write_file_content(file_path, content + existing_content)
        else:
            self._write_file_content(file_path, content)

    def _read_file_content(self, file_path: str) -> str:
        with open(file_path, encoding="utf-8") as file:
            return file.read()

    def _modify_markdown_section(self, file_path: str, section_path: list[str], new_content: str, submode: str) -> None:
        from hermes.chat.interface.markdown.document_updater import MarkdownDocumentUpdater

        updater = MarkdownDocumentUpdater(file_path)

        try:
            was_updated = updater.update_section(section_path, new_content, submode)
            self._notify_markdown_update_result(was_updated, section_path, file_path, submode)
        except ValueError as e:
            self.notifications_printer.print_notification(str(e))
            raise

    def _notify_markdown_update_result(self, was_updated: bool, section_path: list[str], file_path: str, submode: str) -> None:
        if was_updated:
            action = "Updated" if submode == "update_markdown_section" else "Appended to"
            self.notifications_printer.print_notification(f"{action} section {' > '.join(section_path)} in {file_path}")
        else:
            self.notifications_printer.print_notification(
                f"Warning: Section {' > '.join(section_path)} not found in {file_path}. No changes made.",
                color=CLIColors.YELLOW,
            )
