from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode


class ResearchNodeLogger:
    """Logger for research node that saves requests and responses to files"""

    def __init__(self, node: 'ResearchNode'):
        self.node = node
        self._logs_dir = None

    @classmethod
    def load_for_research_node(cls, research_node: "ResearchNode") -> list["ResearchNodeLogger"]:
        """Load logger for a research node"""
        # Create a new logger for the node
        return [cls(research_node)]

    def save(self):
        """No need to save anything for the logger as it saves on each log call"""
        pass

    def _ensure_logs_directory(self) -> Path:
        """Ensure logs_and_debug directory exists for the current problem"""
        node_path = self.node.get_path()
        if not node_path:
            raise ValueError("Node path is not set")

        logs_dir = node_path / "logs_and_debug"
        logs_dir.mkdir(exist_ok=True)
        self._logs_dir = logs_dir
        return logs_dir

    def log_llm_request(self, rendered_messages: list[dict], request_data: dict) -> None:
        """Log an LLM request to a file"""
        logs_dir = self._ensure_logs_directory()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_LLM_Request.md"

        with open(logs_dir / filename, "w", encoding="utf-8") as f:
            f.write("=== LLM REQUEST ===\n\n")
            f.write("== Chat History ==\n")
            for msg in rendered_messages:
                f.write(f"[{msg.get('author', 'unknown')}]: {msg.get('content', '')}\n\n")

            # Also log the request data
            f.write("\n== Request Data ==\n")
            for key, value in request_data.items():
                f.write(f"{key}: {value}\n")

    def log_llm_response(self, response: str) -> None:
        """Log an LLM response to a file"""
        logs_dir = self._ensure_logs_directory()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_LLM_Response.md"

        with open(logs_dir / filename, "w", encoding="utf-8") as f:
            f.write("=== LLM RESPONSE ===\n\n")
            f.write(response)
