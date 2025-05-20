from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent.framework.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode


class ProblemStatus(Enum):
    CREATED = auto()
    READY_TO_START = auto()
    PENDING = auto()
    IN_PROGRESS = auto()
    FINISHED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class ProblemDefinition:
    content: str


class ProblemDefinitionManager:
    """Manages the problem definition for a research node"""

    def __init__(self, node: "ResearchNode", problem_definition: ProblemDefinition):
        self.node = node
        self.problem_definition: ProblemDefinition = problem_definition

    @classmethod
    def load_for_research_node(cls, research_node: "ResearchNode") -> "ProblemDefinitionManager":
        """Load problem definition for a research node"""
        node_path = research_node.get_path()
        md_file = MarkdownFileWithMetadataImpl.load_from_directory(node_path, "Problem Definition")

        return ProblemDefinitionManager(node=research_node, problem_definition=ProblemDefinition(md_file.get_content()))

    def save(self) -> None:
        """Save problem definition to disk"""
        node_path = self.node.get_path()
        if not node_path or not self.problem_definition:
            return

        md_file = MarkdownFileWithMetadataImpl("Problem Definition", self.problem_definition.content)
        md_file.save_file(node_path)

    def append_to_definition(self, content: str) -> None:
        """Append additional content to the problem definition"""
        if not self.problem_definition:
            return

        self.problem_definition.content += "\n\nUPDATE\n" + content
        self.save()
