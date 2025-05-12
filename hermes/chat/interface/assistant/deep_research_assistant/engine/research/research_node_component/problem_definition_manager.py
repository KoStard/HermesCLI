from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode


class ProblemStatus(Enum):
    NOT_STARTED = "NOT_STARTED"  # Problem has not been started yet
    PENDING = "PENDING"  # Problem is temporarily paused (focus moved to child)
    IN_PROGRESS = "IN_PROGRESS"  # Problem is currently being worked on
    FINISHED = "FINISHED"  # Problem has been successfully completed
    FAILED = "FAILED"  # Problem could not be solved
    CANCELLED = "CANCELLED"  # Problem was determined to be unnecessary


@dataclass
class ProblemDefinition:
    content: str


class ProblemDefinitionManager:
    """Manages the problem definition for a research node"""

    def __init__(self, node: 'ResearchNode', problem_definition: ProblemDefinition, status: ProblemStatus):
        self.node = node
        self.problem_definition: ProblemDefinition = problem_definition
        self.status: ProblemStatus = status

    @classmethod
    def load_for_research_node(cls, research_node: 'ResearchNode') -> "ProblemDefinitionManager":
        """Load problem definition for a research node"""
        node_path = research_node.get_path()
        md_file = MarkdownFileWithMetadataImpl.load_from_directory(node_path, "Problem Definition")

        # Get status as proper enum
        status_value = md_file.get_metadata().get('status', ProblemStatus.NOT_STARTED.value)
        try:
            status = ProblemStatus(status_value)
        except ValueError:
            status = ProblemStatus.NOT_STARTED

        return ProblemDefinitionManager(
            node=research_node,
            problem_definition=ProblemDefinition(md_file.get_content()),
            status=status
        )


    def save(self) -> None:
        """Save problem definition to disk"""
        node_path = self.node.get_path()
        if not node_path or not self.problem_definition or not self.status:
            return

        md_file = MarkdownFileWithMetadataImpl("Problem Definition", self.problem_definition.content)
        md_file.add_property("status", self.status.value)
        md_file.save_file(node_path)

    def append_to_definition(self, content: str) -> None:
        """Append additional content to the problem definition"""
        if not self.problem_definition:
            return

        self.problem_definition.content += "\n\nUPDATE\n" + content
        self.save()

    def update_status(self, status: ProblemStatus) -> None:
        """Update the problem status"""
        self.status = status
        self.save()
