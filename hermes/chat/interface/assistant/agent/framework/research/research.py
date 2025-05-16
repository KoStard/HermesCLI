from pathlib import Path

from hermes.chat.interface.assistant.agent.framework.research.file_system.disk_file_system import DiskFileSystem
from hermes.chat.interface.assistant.agent.framework.research.research_node import ResearchNodeImpl
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.agent.framework.research.research_project_component.external_file import (
    ExternalFilesManager,
)
from hermes.chat.interface.assistant.agent.framework.research.research_project_component.knowledge_base import (
    KnowledgeBase,
)
from hermes.chat.interface.assistant.agent.framework.research.research_project_component.permanent_log import (
    NodePermanentLogs,
)

from . import Research, ResearchNode


class ResearchImpl(Research):
    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory
        self.file_system = DiskFileSystem()
        self.root_node = None
        self._permanent_logs = NodePermanentLogs(root_directory / "_permanent_logs.txt")
        self._research_initiated = False

        # Create instances for knowledge base and external files
        self._knowledge_base = KnowledgeBase(self.file_system, self.root_directory / "_knowledge_base.md")
        self._external_files_manager = ExternalFilesManager(self.file_system, self.root_directory / "_ExternalFiles")

    def research_already_exists(self) -> bool:
        """Check if research data already exists in the root directory"""
        # Look for the research metadata file
        return self.root_directory.exists() and not self.file_system.is_empty(self.root_directory)

    def research_initiated(self) -> bool:
        """Return whether research has been initiated"""
        return self._research_initiated and self.root_node is not None

    def initiate_research(self, root_node: ResearchNode):
        """Initialize a new research project"""
        self.root_node = root_node
        assert root_node.get_path() == self.root_directory

        # Create the necessary directories
        self._create_directory_structure()

        self._research_initiated = True

    def load_existing_research(self):
        """Load an existing research project"""
        # Load knowledge base and external files
        self._knowledge_base.load_entries()
        self._external_files_manager.load_external_files()

        # Load the root node from disk using the node's static loading method
        root_node = ResearchNodeImpl.load_from_directory(self.root_directory)

        self.initiate_research(root_node)

    def get_root_node(self) -> ResearchNode:
        """Get the root node of the research"""
        if not self.research_initiated():
            raise ValueError("Research not initiated")
        assert self.root_node is not None
        return self.root_node

    def get_root_directory(self) -> Path:
        return self.root_directory

    def get_permanent_logs(self) -> NodePermanentLogs:
        """Get the permanent logs for the research"""
        return self._permanent_logs

    def get_knowledge_base(self) -> KnowledgeBase:
        return self._knowledge_base

    def get_external_file_manager(self):
        return self._external_files_manager

    def search_artifacts(self, name: str) -> list[tuple[ResearchNode, Artifact]]:
        """
        Search for artifacts with matching names across all research nodes.

        Args:
            name: The name to search for in artifact names

        Returns:
            List of (node, artifact) tuples for all matching artifacts
        """
        if not self.research_initiated():
            return []

        result = []
        assert self.root_node is not None
        self._search_artifacts_recursive(self.root_node, name.lower(), result)
        return result

    def _search_artifacts_recursive(self, node: ResearchNode, search_term: str, result: list[tuple[ResearchNode, Artifact]]) -> None:
        """
        Recursively search for artifacts in a node and its children.

        Args:
            node: The node to search in
            search_term: Lowercase search term to match against artifact names
            result: List to collect matching (node, artifact) tuples
        """
        # Check artifacts in current node
        for artifact in node.get_artifacts():
            if search_term in artifact.name.lower():
                result.append((node, artifact))

        # Recursively search in child nodes
        for child in node.list_child_nodes():
            self._search_artifacts_recursive(child, search_term, result)

    def _create_directory_structure(self):
        """Create the necessary directory structure for the research"""
        # Create the root directory if it doesn't exist
        if not self.file_system.directory_exists(self.root_directory):
            self.file_system.create_directory(self.root_directory)
