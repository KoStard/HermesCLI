import os
from datetime import datetime
from pathlib import Path


class NodePermanentLogs:
    """Maintains a log of permanent entries for the research project"""

    def __init__(self, log_file_path: Path):
        self._logs = []
        self._log_file_path = log_file_path

        if os.path.exists(log_file_path):
            self.load()

    def add_log(self, content: str) -> None:
        """Add a new log entry with timestamp and save to file"""
        content = content.replace("\n", "; ")

        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] {content}"
        self._logs.append(entry)

        self._save_entry(entry)

    def get_logs(self) -> list[str]:
        """Get all logs"""
        return self._logs.copy()

    def load(self) -> None:
        """Load logs from file"""
        try:
            if os.path.exists(self._log_file_path):
                with open(self._log_file_path, encoding="utf-8") as file:
                    self._logs = [line.strip() for line in file.readlines() if line.strip()]
        except Exception as e:
            print(f"Error loading permanent logs: {e}")

    def save(self) -> None:
        """Save all logs to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._log_file_path), exist_ok=True)

            # Write all logs to file
            with open(self._log_file_path, "w", encoding="utf-8") as file:
                for log in self._logs:
                    file.write(f"{log}\n")
        except Exception as e:
            print(f"Error saving permanent logs: {e}")

    def _save_entry(self, entry: str) -> None:
        """Append a single entry to the log file - more efficient than rewriting the whole file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._log_file_path), exist_ok=True)

            # Append to file
            with open(self._log_file_path, "a", encoding="utf-8") as file:
                file.write(f"{entry}\n")
        except Exception as e:
            print(f"Error appending to permanent logs: {e}")
