from pathlib import Path

from hermes.chat.interface.assistant.agent.framework.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import (
    Artifact,
    ArtifactManager,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.criteria_manager import (
    CriteriaManager,
    Criterion,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.history.history import (
    ResearchNodeHistory,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.logger import ResearchNodeLogger
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemDefinitionManager,
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.state import (
    NodeState,
    StateManager,
)

from . import ResearchNode


class ResearchNodeImpl(ResearchNode):
    def __init__(self, problem: ProblemDefinition, title: str, parent: 'ResearchNode | None', path: Path) -> None:
        self.children: list[ResearchNode] = []
        self.parent: ResearchNode | None = parent
        self._path: Path = path
        self._title = title

        # Initialize history with proper file path
        history_path = path / "history.json"
        self._history: ResearchNodeHistory = ResearchNodeHistory(history_path)

        # Component managers
        self.artifact_manager: ArtifactManager = ArtifactManager(self)
        self.criteria_manager: CriteriaManager = CriteriaManager(self)
        self.logger: ResearchNodeLogger = ResearchNodeLogger(self)
        self.problem_manager: ProblemDefinitionManager = ProblemDefinitionManager(self, problem, ProblemStatus.NOT_STARTED)
        self.state_manager: StateManager = StateManager(self)

        # Initialize file system components if path is set
        self._init_components()

    @classmethod
    def load_from_directory(cls, node_path: Path) -> 'ResearchNode':
        return cls._load_from_directory(node_path, None)

    @classmethod
    def _load_from_directory(cls, node_path: Path, parent_node: 'ResearchNode | None' = None) -> 'ResearchNode':
        """
        Load a node and all its children from a directory.

        Args:
            node_path: Path to the node directory
            parent_node: Parent node, or None for the root node

        Returns:
            Loaded ResearchNode instance
        """
        # Check if problem definition exists using the new API
        if not MarkdownFileWithMetadataImpl.file_exists(node_path, "Problem Definition"):
            raise FileNotFoundError(f"Problem definition file not found at {node_path}")

        # Load the problem definition file
        md_file = MarkdownFileWithMetadataImpl.load_from_directory(node_path, "Problem Definition")
        problem_def = ProblemDefinition(content=md_file.get_content())

        # Get status from metadata
        status_str = md_file.get_metadata().get('status', ProblemStatus.NOT_STARTED.value)
        try:
            status = ProblemStatus(status_str)
        except ValueError:
            status = ProblemStatus.NOT_STARTED

        # Create the node with the loaded problem definition
        node = ResearchNodeImpl(
            problem=problem_def,
            title=node_path.name,
            path=node_path,
            parent=parent_node
        )

        # Update node status (which might have been loaded incorrectly during initialization)
        node.set_problem_status(status)

        # Load child nodes
        cls._load_child_nodes_for(node)

        return node

    @classmethod
    def _load_child_nodes_for(cls, parent_node: 'ResearchNode') -> None:
        """
        Load child nodes for a parent node from the file system.

        Args:
            parent_node: The parent node to load children for
        """
        subproblems_dir = parent_node.get_path() / "Subproblems"
        if not subproblems_dir.exists():
            return

        for child_dir in subproblems_dir.iterdir():
            if child_dir.is_dir() and MarkdownFileWithMetadataImpl.file_exists(child_dir, "Problem Definition"):
                try:
                    # Load the child node from disk
                    child_node = cls._load_from_directory(child_dir, parent_node)

                    # Add child to parent
                    parent_node.add_child_node(child_node)
                except Exception as e:
                    print(f"Error loading child node {child_dir.name}: {e}")

    def _init_components(self):
        """Initialize node components"""
        if not self._path.exists():
            self._path.mkdir(parents=True, exist_ok=True)

        # Create artifacts directory
        artifacts_dir = self._path / "Artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        # Create subproblems directory
        subproblems_dir = self._path / "Subproblems"
        subproblems_dir.mkdir(exist_ok=True)

        # Create logs directory
        logs_dir = self._path / "logs_and_debug"
        logs_dir.mkdir(exist_ok=True)

        # Save the problem definition to disk if it's a new node
        problem_def_path = self._path / "Problem Definition.md"
        if not problem_def_path.exists():
            self.problem_manager.save()
        else:
            # If it exists, load from disk to ensure we have the latest version
            self.problem_manager = ProblemDefinitionManager.load_for_research_node(self)

        # Load all components from disk
        self.criteria_manager = CriteriaManager.load_for_research_node(self)[0]
        self.artifact_manager = ArtifactManager.load_for_research_node(self)[0]
        self.state_manager = StateManager.load_for_research_node(self)[0]
        self.logger = ResearchNodeLogger.load_for_research_node(self)[0]

    def list_child_nodes(self) -> list[ResearchNode]:
        return self.children

    def add_child_node(self, child_node: ResearchNode):
        self.children.append(child_node)
        # Each child node manages its own saving through its components

    def create_child_node(self, title: str, problem_content: str) -> ResearchNode:
        """
        Create a new child node with the given title and problem content.
        This method handles path construction and node initialization internally.

        Args:
            title: Title of the child node
            problem_content: Content for the child node's problem definition

        Returns:
            The newly created child node
        """
        # Create problem definition

        problem_def = ProblemDefinition(content=problem_content)

        # Construct proper path within Subproblems directory
        subproblems_dir = self._path / "Subproblems"
        child_path = subproblems_dir / title

        # Create the new node
        child_node = ResearchNodeImpl(
            problem=problem_def,
            title=title,
            path=child_path,
            parent=self
        )

        # Set initial status
        child_node.set_problem_status(ProblemStatus.NOT_STARTED)

        # Add to children
        self.add_child_node(child_node)

        return child_node

    def get_parent(self) -> ResearchNode | None:
        return self.parent

    def get_artifacts(self) -> list[Artifact]:
        return self.artifact_manager.artifacts

    def get_criteria(self) -> list[Criterion]:
        return self.criteria_manager.criteria

    def mark_criterion_as_done(self, index: int) -> bool:
        """
        Mark criterion as done and return success

        Args:
            index: Index of the criterion to mark as done

        Returns:
            True if successful, False otherwise
        """
        return self.criteria_manager.mark_criterion_as_done(index)

    def get_criteria_met_count(self) -> int:
        return self.criteria_manager.get_criteria_met_count()

    def get_criteria_total_count(self) -> int:
        return self.criteria_manager.get_criteria_total_count()

    def append_to_problem_definition(self, content: str) -> None:
        """
        Append additional content to the problem definition

        Args:
            content: The content to append
        """
        self.problem_manager.append_to_definition(content)

    def get_problem(self) -> ProblemDefinition:
        return self.problem_manager.problem_definition

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifact_manager.add_artifact(artifact)

        # Default to open status in state manager
        self.state_manager.set_artifact_status(artifact, True)

    def add_criterion(self, criterion: Criterion):
        """
        Add a criterion and return its index
        If the criterion already exists, return its index
        """
        self.criteria_manager.add_criterion(criterion)

    def get_title(self) -> str:
        return self._title

    def get_node_state(self) -> NodeState:
        return self.state_manager.get_state()

    def set_problem_status(self, status: ProblemStatus):
        self.problem_manager.update_status(status)
        self.state_manager.set_problem_status(status)

    def get_problem_status(self) -> ProblemStatus:
        return self.state_manager.get_problem_status()

    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        self.state_manager.set_artifact_status(artifact, is_open)

    def get_history(self) -> ResearchNodeHistory:
        return self._history

    def get_path(self) -> Path:
        return self._path

    def get_logger(self) -> ResearchNodeLogger:
        return self.logger

    def get_depth_from_root(self) -> int:
        parent = self.get_parent()
        if parent:
            return parent.get_depth_from_root() + 1
        return 0
