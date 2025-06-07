from pathlib import Path
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent_old.framework.research.file_system.dual_directory_file_system import DualDirectoryFileSystem
from hermes.chat.interface.assistant.agent_old.framework.research.research_node import ResearchNodeImpl
from hermes.chat.interface.assistant.agent_old.framework.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.agent_old.framework.research.research_project_component.external_file import (
    ExternalFilesManager,
)
from hermes.chat.interface.assistant.agent_old.framework.research.research_project_component.knowledge_base import (
    KnowledgeBase,
)
from hermes.chat.interface.assistant.agent_old.framework.research.research_project_component.permanent_log import (
    NodePermanentLogs,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent_old.framework.research.repo import Repo
    from hermes.chat.interface.assistant.agent_old.framework.task_tree import TaskTree

from . import Research, ResearchNode


class ResearchImpl(Research):
    def __init__(
        self, root_directory: Path, dual_directory_file_system: DualDirectoryFileSystem, shared_knowledge_base: KnowledgeBase, repo: "Repo"
    ):
        # Initialize without creating a new knowledge base
        self.root_directory = root_directory
        self.file_system = dual_directory_file_system._disk_fs
        self.dual_directory_file_system = dual_directory_file_system
        self.root_node = None
        self._permanent_logs = NodePermanentLogs(root_directory / "_permanent_logs.txt")
        self._has_root_problem_defined = False

        # Use the shared knowledge base
        self._shared_knowledge_base = shared_knowledge_base

        # Reference to parent repo
        self._repo = repo

        # Still maintain own external files
        self._external_files_manager = ExternalFilesManager(self.file_system, root_directory / "_ExternalFiles")

    def research_already_exists(self) -> bool:
        """Check if research data already exists in the root directory"""
        return self.root_directory.exists() and not self.file_system.is_empty(self.root_directory)

    def has_root_problem_defined(self) -> bool:
        """Return whether the root problem has been defined"""
        return self._has_root_problem_defined and self.root_node is not None

    def initiate_research(self, root_node: ResearchNode):
        """Initialize a new research project"""
        self.root_node = root_node

        # Create the necessary directories
        self._create_directory_structure()

        self._has_root_problem_defined = True

    def load_existing_research(self, task_tree: "TaskTree"):
        """Load an existing research project"""
        # Load knowledge base and external files
        self._external_files_manager.load_external_files()

        root_node = ResearchNodeImpl.load_from_directory(self.root_directory, task_tree, self.dual_directory_file_system)

        self.initiate_research(root_node)

    def get_root_node(self) -> ResearchNode:
        """Get the root node of the research"""
        if not self.has_root_problem_defined():
            raise ValueError("Root problem not defined")
        assert self.root_node is not None
        return self.root_node

    def get_root_directory(self) -> Path:
        return self.root_directory

    def get_permanent_logs(self) -> NodePermanentLogs:
        """Get the permanent logs for the research"""
        return self._permanent_logs

    def get_knowledge_base(self) -> KnowledgeBase:
        return self._shared_knowledge_base

    def get_external_file_manager(self):
        return self._external_files_manager

    def search_artifacts(self, name: str) -> list[tuple[ResearchNode, Artifact]]:
        """
        Search for artifacts with matching names across all research nodes.
        Now searches in the Results/ directory structure.

        Args:
            name: The name to search for in artifact names

        Returns:
            List of (node, artifact) tuples for all matching artifacts
        """
        if not self.has_root_problem_defined():
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

    def get_repo(self) -> "Repo | None":
        return self._repo

    def search_artifacts_including_siblings(self, name: str) -> list[tuple[str, ResearchNode, Artifact]]:
        """
        Search for artifacts in this research and all sibling research instances.

        Returns:
            List of (research_name, node, artifact) tuples
        """
        return self._repo.search_artifacts_across_all(name)
