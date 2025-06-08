from pathlib import Path

from hermes.chat.interface.assistant.deep_research.research import Research, ResearchNode
from hermes.chat.interface.assistant.deep_research.research.file_system.dual_directory_file_system import DualDirectoryFileSystem
from hermes.chat.interface.assistant.deep_research.research.research import ResearchImpl
from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.deep_research.research.research_project_component.knowledge_base import KnowledgeBase
from hermes.chat.interface.assistant.deep_research.task_tree.task_tree import TaskTreeImpl


class Repo:
    """Root repository that manages multiple Research instances.
    All Research instances share a common knowledge base and can see each other's artifacts.
    """

    def __init__(self, root_directory: Path, dual_directory_file_system: DualDirectoryFileSystem):
        self.root_directory = root_directory
        self.dual_directory_file_system = dual_directory_file_system
        self._research_instances: dict[str, Research] = {}
        self._task_trees: dict[str, TaskTreeImpl] = {}

        # Shared knowledge base for all research instances
        self._shared_knowledge_base = KnowledgeBase(dual_directory_file_system._disk_fs, dual_directory_file_system.root_directory)
        self._shared_knowledge_base.load_entries()

        # Load existing research instances from disk
        self._load_existing_research_instances()

    def create_research(self, name: str) -> Research:
        """Create a new Research instance under this Repo.

        Args:
            name: Name of the research instance

        Returns:
            The created Research instance
        """
        if name in self._research_instances:
            print(f"Research instance '{name}' already exists")
            return self._research_instances[name]

        # Create a subdirectory for this research
        research_path = self.dual_directory_file_system.get_path_in_research_from_root(Path(name))

        # Create the research instance with shared knowledge base
        research = ResearchImpl(
            root_directory=research_path,
            dual_directory_file_system=self.dual_directory_file_system,
            shared_knowledge_base=self._shared_knowledge_base,
            repo=self,
        )

        # Create and store task tree for this research
        self._task_trees[name] = TaskTreeImpl(research)

        self._research_instances[name] = research
        return research

    def get_research(self, name: str) -> Research | None:
        """Get a research instance by name."""
        return self._research_instances.get(name)

    def list_research_instances(self) -> list[str]:
        """List all research instance names."""
        return list(self._research_instances.keys())

    def _is_valid_research_directory(self, path: Path) -> bool:
        """Check if the given path is a valid research directory.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path is a valid research directory, False otherwise
        """
        # Must be a directory
        if not path.is_dir():
            return False

        # Skip system files/directories
        if path.name.startswith("_"):
            return False

        return True

    def _load_research_from_path(self, research_path: Path) -> None:
        """Load a research instance from the given path.
        
        Args:
            research_path: Path to the research directory
        """
        research_name = research_path.name

        # Create research instance
        research = ResearchImpl(
            root_directory=research_path,
            dual_directory_file_system=self.dual_directory_file_system,
            shared_knowledge_base=self._shared_knowledge_base,
            repo=self,
        )

        # Create task tree for this research
        task_tree = TaskTreeImpl(research)
        self._task_trees[research_name] = task_tree

        # Load the research if it exists on disk
        if research.research_already_exists():
            research.load_existing_research(task_tree)

        self._research_instances[research_name] = research

    def _load_existing_research_instances(self):
        """Scan the research directory and load existing research instances.
        This allows the repo to discover research instances that were created in previous sessions.
        """
        repo_path = self.dual_directory_file_system.get_repo_path()

        # If the research directory doesn't exist, there are no existing instances
        if not self.dual_directory_file_system.directory_exists(repo_path):
            return

        # Scan for subdirectories that contain research data
        for research_path in repo_path.iterdir():
            if self._is_valid_research_directory(research_path):
                self._load_research_from_path(research_path)

    def get_all_artifacts(self) -> dict[str, list[tuple[ResearchNode, Artifact]]]:
        """Get all artifacts from all research instances.

        Returns:
            Dictionary mapping research name to list of (node, artifact) tuples
        """
        all_artifacts = {}
        for name, research in self._research_instances.items():
            if research.has_root_problem_defined():
                artifacts = []
                root_node = research.get_root_node()
                self._collect_artifacts_recursive(root_node, artifacts)
                all_artifacts[name] = artifacts
        return all_artifacts

    def _collect_artifacts_recursive(self, node: ResearchNode, artifacts: list[tuple[ResearchNode, Artifact]]):
        """Recursively collect artifacts from a node and its children."""
        for artifact in node.get_artifacts():
            artifacts.append((node, artifact))
        for child in node.list_child_nodes():
            self._collect_artifacts_recursive(child, artifacts)

    def search_artifacts_across_all(self, name: str) -> list[tuple[str, ResearchNode, Artifact]]:
        """Search for artifacts across all research instances.

        Args:
            name: The name to search for in artifact names

        Returns:
            List of (research_name, node, artifact) tuples
        """
        results = []
        for research_name, research in self._research_instances.items():
            if research.has_root_problem_defined():
                for node, artifact in research.search_artifacts(name):
                    results.append((research_name, node, artifact))
        return results

    def get_task_tree(self, research_name: str) -> TaskTreeImpl | None:
        """Get the task tree for a specific research instance."""
        return self._task_trees.get(research_name)
