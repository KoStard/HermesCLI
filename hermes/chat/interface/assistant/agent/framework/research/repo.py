from pathlib import Path

from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent.framework.research.file_system.dual_directory_file_system import DualDirectoryFileSystem
from hermes.chat.interface.assistant.agent.framework.research.research import ResearchImpl
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.agent.framework.research.research_project_component.external_file import ExternalFilesManager
from hermes.chat.interface.assistant.agent.framework.research.research_project_component.knowledge_base import KnowledgeBase
from hermes.chat.interface.assistant.agent.framework.research.research_project_component.permanent_log import NodePermanentLogs
from hermes.chat.interface.assistant.agent.framework.task_tree.task_tree import TaskTreeImpl


class Repo:
    """
    Root repository that manages multiple Research instances.
    All Research instances share a common knowledge base and can see each other's artifacts.
    """

    def __init__(self, root_directory: Path, dual_directory_file_system: DualDirectoryFileSystem):
        self.root_directory = root_directory
        self.dual_directory_file_system = dual_directory_file_system
        self._research_instances: dict[str, Research] = {}
        self._task_trees: dict[str, TaskTreeImpl] = {}

        # Shared knowledge base for all research instances
        self._shared_knowledge_base = KnowledgeBase(
            dual_directory_file_system._disk_fs,
            dual_directory_file_system.get_research_path(Path("_shared_knowledge_base.md"))
        )

        # Load existing research instances from disk
        self._load_existing_research_instances()

    def create_research(self, name: str) -> Research:
        """
        Create a new Research instance under this Repo.

        Args:
            name: Name of the research instance

        Returns:
            The created Research instance
        """
        if name in self._research_instances:
            raise ValueError(f"Research instance '{name}' already exists")

        # Create a subdirectory for this research
        research_path = self.dual_directory_file_system.get_research_path(Path(name))
        research_dual_fs = DualDirectoryFileSystem(research_path)

        # Create the research instance with shared knowledge base
        research = RepoResearchImpl(
            root_directory=research_path,
            dual_directory_file_system=research_dual_fs,
            shared_knowledge_base=self._shared_knowledge_base,
            parent_repo=self
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

    def _load_existing_research_instances(self):
        """
        Scan the research directory and load existing research instances.
        This allows the repo to discover research instances that were created in previous sessions.
        """
        research_base_path = self.dual_directory_file_system.get_research_path()

        # If the research directory doesn't exist, there are no existing instances
        if not self.dual_directory_file_system.directory_exists(research_base_path):
            return

        # Scan for subdirectories that contain research data
        for item in research_base_path.iterdir():
            if not item.is_dir():
                continue

            # Skip system files/directories
            if item.name.startswith('_'):
                continue

            research_name = item.name

            # Create and fully load the research instance
            research_dual_fs = DualDirectoryFileSystem(item)
            research = RepoResearchImpl(
                root_directory=item,
                dual_directory_file_system=research_dual_fs,
                shared_knowledge_base=self._shared_knowledge_base,
                parent_repo=self
            )

            # Create task tree for this research
            task_tree = TaskTreeImpl(research)
            self._task_trees[research_name] = task_tree

            # Load the research if it exists on disk
            if research.research_already_exists():
                research.load_existing_research(task_tree)

            self._research_instances[research_name] = research

    def get_all_artifacts(self) -> dict[str, list[tuple[ResearchNode, Artifact]]]:
        """
        Get all artifacts from all research instances.

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
        """
        Search for artifacts across all research instances.

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


class RepoResearchImpl(ResearchImpl):
    """
    Extended Research implementation that's aware of its parent Repo.
    Uses a shared knowledge base and can access artifacts from sibling research instances.
    """

    def __init__(
        self,
        root_directory: Path,
        dual_directory_file_system: DualDirectoryFileSystem,
        shared_knowledge_base: KnowledgeBase,
        parent_repo: Repo
    ):
        # Initialize without creating a new knowledge base
        self.root_directory = root_directory
        self.file_system = dual_directory_file_system._disk_fs
        self.dual_directory_file_system = dual_directory_file_system
        self.root_node = None
        self._permanent_logs = NodePermanentLogs(
            self.dual_directory_file_system.get_research_path(Path("_permanent_logs.txt"))
        )
        self._has_root_problem_defined = False

        # Use the shared knowledge base
        self._knowledge_base = shared_knowledge_base

        # Reference to parent repo
        self.parent_repo = parent_repo

        # Still maintain own external files
        self._external_files_manager = ExternalFilesManager(
            self.file_system,
            self.dual_directory_file_system.get_research_path(Path("_ExternalFiles"))
        )

    def get_knowledge_base(self) -> KnowledgeBase:
        """Return the shared knowledge base."""
        return self._knowledge_base

    def search_artifacts_including_siblings(self, name: str) -> list[tuple[str, ResearchNode, Artifact]]:
        """
        Search for artifacts in this research and all sibling research instances.

        Returns:
            List of (research_name, node, artifact) tuples
        """
        return self.parent_repo.search_artifacts_across_all(name)
