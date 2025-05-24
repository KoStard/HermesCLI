from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.events.engine_commands.base import EngineCommandEvent

if TYPE_CHECKING:
    from hermes.chat.conversation_orchestrator import ConversationOrchestrator


@dataclass
class FileEditEvent(EngineCommandEvent):
    """Event for file operations like create, append or update markdown sections"""

    file_path: str
    content: str
    mode: str  # 'create', 'append', 'update_markdown_section', 'append_markdown_section'
    submode: str | None = None  # Optional, only for specific use cases
    section_path: list[str] | None = None  # For markdown section updates, e.g. ['Introduction', 'Overview', '__preface']

    def execute(self, orchestrator: "ConversationOrchestrator") -> None:
        if self.mode == "create":
            orchestrator.file_operations_handler.create_file(self.file_path, self.content)
        elif self.mode == "append":
            orchestrator.file_operations_handler.append_to_file(self.file_path, self.content)
        elif self.mode == "update_markdown_section":
            orchestrator.file_operations_handler.update_markdown_section(
                self.file_path,
                self.section_path,
                self.content,
                self.submode,
            )
        elif self.mode == "prepend":
            orchestrator.file_operations_handler.handle_file_prepend(self.file_path, self.content)