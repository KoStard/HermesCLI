from datetime import datetime
from pathlib import Path


class DeepResearchLogger:
    """Logger for Deep Research Assistant that saves requests and responses to files"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def ensure_logs_directory(self, node_path: Path | None) -> Path | None:
        """Ensure logs_and_debug directory exists for the current problem"""
        if not node_path:
            return None

        logs_dir = node_path / "logs_and_debug"
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
        return logs_dir

    def log_llm_request(
        self,
        node_path: Path | None,
        rendered_messages: list[dict],
        request_data: dict,
    ) -> None:
        """Log an LLM request to a file"""
        logs_dir = self.ensure_logs_directory(node_path)
        if not logs_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_LLM_Request.md"

        with open(logs_dir / filename, "w", encoding="utf-8") as f:
            f.write("=== LLM REQUEST ===\n\n")
            f.write("== Chat History ==\n")
            for msg in rendered_messages:
                f.write(f"[{msg.get('author', 'unknown')}]: {msg.get('content', '')}\n\n")

    def log_llm_response(self, node_path: Path | None, response: str) -> None:
        """Log an LLM response to a file"""
        logs_dir = self.ensure_logs_directory(node_path)
        if not logs_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_LLM_Response.md"

        with open(logs_dir / filename, "w", encoding="utf-8") as f:
            f.write("=== LLM RESPONSE ===\n\n")
            f.write(response)
