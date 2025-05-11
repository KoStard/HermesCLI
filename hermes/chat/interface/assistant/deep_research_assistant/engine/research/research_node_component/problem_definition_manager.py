from pathlib import Path
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition import (
    ProblemDefinition,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.state import ProblemStatus

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode


class ProblemDefinitionManager:
    """Manages the problem definition for a research node"""

    def __init__(self, node: 'ResearchNode'):
        self.node = node
        self.problem_definition: ProblemDefinition | None = None
        self.title: str | None = None
        self.status: ProblemStatus | None = None
        
    @classmethod
    def load_for_research_node(cls, research_node: 'ResearchNode') -> "ProblemDefinitionManager":
        """Load problem definition for a research node"""
        manager = cls(research_node)
        
        # Set initial values from node
        manager.problem_definition = research_node.get_problem()
        manager.title = research_node.get_title()
        manager.status = research_node.get_problem_status()
        
        return manager
        
    def save(self) -> None:
        """Save problem definition to disk"""
        node_path = self.node.get_path()
        if not node_path or not self.problem_definition or not self.title or not self.status:
            return
            
        # Save problem definition with metadata
        problem_def_path = node_path / "Problem Definition.md"

        md_file = MarkdownFileWithMetadataImpl(self.title, self.problem_definition.content)
        md_file.add_property("status", self.status.value)
        md_file.save_file(str(problem_def_path))
        
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
