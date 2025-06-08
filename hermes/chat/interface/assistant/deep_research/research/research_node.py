import threading
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.research.file_system.dual_directory_file_system import DualDirectoryFileSystem
from hermes.chat.interface.assistant.deep_research.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import (
    Artifact,
    ArtifactManager,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_component.criteria_manager import (
    CriteriaManager,
    Criterion,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_component.history.history import (
    ResearchNodeHistory,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_component.logger import ResearchNodeLogger
from hermes.chat.interface.assistant.deep_research.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemDefinitionManager,
    ProblemStatus,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_component.state import (
    NodeState,
    StateManager,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.task_tree import TaskTree

from . import ResearchNode, ResearchNodeStatusChangeEvent


class ResearchNodeImpl(ResearchNode):
    def __init__(
        self,
        problem: ProblemDefinition,
        title: str,
        parent: "ResearchNode | None",
        path: Path,
        task_tree: "TaskTree",
        dual_directory_fs: "DualDirectoryFileSystem",
    ) -> None:
        self.children: list[ResearchNode] = []
        self.parent: ResearchNode | None = parent
        self._path: Path = path
        self._title = self._prepare_title(title)

        # Initialize history with proper file path
        history_path = path / "history.json"
        self._history: ResearchNodeHistory = ResearchNodeHistory(history_path)

        # Store dual directory file system reference
        self._dual_directory_fs = dual_directory_fs

        # Component managers
        self.artifact_manager: ArtifactManager = ArtifactManager(self, self._dual_directory_fs)
        self.criteria_manager: CriteriaManager = CriteriaManager(self)
        self.logger: ResearchNodeLogger = ResearchNodeLogger(self)
        self.problem_manager: ProblemDefinitionManager = ProblemDefinitionManager(self, problem)
        self._state_manager: StateManager = StateManager(self)
        self._events_queue: Queue | None = None
        self.task_tree = task_tree
        self.task_tree.register_node(self)
        self._status_lock = threading.RLock()

        # Initialize file system components if path is set
        self._init_components()

    def _prepare_title(self, title: str) -> str:
        if len(title) > 200:
            title = title[:200] + "..."
        return title

    def _init_components(self):
        """Initialize node components"""
        if not self._path.exists():
            self._path.mkdir(parents=True, exist_ok=True)

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
        self.artifact_manager = ArtifactManager.load_for_research_node(self, self._dual_directory_fs)[0]
        self._state_manager = StateManager.load_for_research_node(self)[0]
        self.logger = ResearchNodeLogger.load_for_research_node(self)[0]

    def get_id(self) -> str:
        return self._state_manager.get_id()

    @classmethod
    def load_from_directory(cls, node_path: Path, task_tree: "TaskTree", dual_directory_fs: "DualDirectoryFileSystem") -> "ResearchNode":
        return cls._load_from_directory(node_path, task_tree, dual_directory_fs)

    @classmethod
    def _load_from_directory(
        cls,
        node_path: Path,
        task_tree: "TaskTree",
        dual_directory_fs: "DualDirectoryFileSystem",
        parent_node: "ResearchNode | None" = None,
    ) -> "ResearchNode":
        """Load a node and all its children from a directory.

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

        node = ResearchNodeImpl(
            problem=problem_def,
            title=node_path.name,
            path=node_path,
            parent=parent_node,
            task_tree=task_tree,
            dual_directory_fs=dual_directory_fs,
        )

        cls._load_child_nodes_for(node, task_tree, dual_directory_fs)

        return node

    @classmethod
    def _load_child_nodes_for(
        cls,
        parent_node: "ResearchNode",
        task_tree: "TaskTree",
        dual_directory_fs: "DualDirectoryFileSystem",
    ) -> None:
        """Load child nodes for a parent node from the file system.

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
                    child_node = cls._load_from_directory(child_dir, task_tree, dual_directory_fs, parent_node)

                    # Add child to parent
                    parent_node.add_child_node(child_node)
                except Exception as e:
                    print(f"Error loading child node {child_dir.name}: {e}")

    def list_child_nodes(self) -> list[ResearchNode]:
        return self.children

    def add_child_node(self, child_node: ResearchNode):
        self.children.append(child_node)
        # Each child node manages its own saving through its components

    def create_child_node(self, title: str, problem_content: str) -> ResearchNode:
        """Create a new child node with the given title and problem content.
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
            parent=self,
            task_tree=self.task_tree,
            dual_directory_fs=self._dual_directory_fs,
        )

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
        """Mark criterion as done and return success

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

    def append_to_problem_definition(self, content: str):
        """Append additional content to the problem definition

        Args:
            content: The content to append
        """
        self.problem_manager.append_to_definition(content)

    def get_problem(self) -> ProblemDefinition:
        return self.problem_manager.problem_definition

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifact_manager.add_artifact(artifact)

        # Default to open status in state manager
        self._state_manager.set_artifact_status(artifact, True)

    def add_criterion(self, criterion: Criterion):
        """Add a criterion and return its index
        If the criterion already exists, return its index
        """
        self.criteria_manager.add_criterion(criterion)

    def get_title(self) -> str:
        return self._title

    def get_node_state(self) -> NodeState:
        with self._status_lock:
            return self._state_manager.get_state()

    def set_problem_status(self, status: ProblemStatus):
        with self._status_lock:
            if status == self.get_problem_status():
                return
            self._state_manager.set_problem_status(status)
            assert self._events_queue
            self._events_queue.put(ResearchNodeStatusChangeEvent())
            if self.parent and status in {ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED}:
                self.parent.remove_child_node_to_wait(self)

    def get_problem_status(self) -> ProblemStatus:
        with self._status_lock:
            return self._state_manager.get_problem_status()

    def add_child_node_to_wait(self, child_node: "ResearchNode"):
        with self._status_lock:
            self._state_manager.add_child_node_to_wait(child_node)
            self.set_problem_status(ProblemStatus.PENDING)

    def remove_child_node_to_wait(self, child_node: "ResearchNode"):
        with self._status_lock:
            if not self._state_manager.remove_child_node_to_wait(child_node):
                return
            if not self._get_child_node_ids_to_wait() and self.get_problem_status() == ProblemStatus.PENDING:
                self.set_problem_status(ProblemStatus.READY_TO_START)

    def _get_child_node_ids_to_wait(self) -> set[str]:
        return self._state_manager.get_state().pending_child_node_ids

    def get_resolution_message(self) -> str | None:
        """Get the resolution message for this node from the state manager."""
        return self._state_manager.get_resolution_message()

    def set_resolution_message(self, message: str | None) -> None:
        """Set the resolution message for this node via the state manager."""
        self._state_manager.set_resolution_message(message)

    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        self._state_manager.set_artifact_status(artifact, is_open)

    def get_artifact_status(self, artifact: Artifact) -> bool:
        return self._state_manager.get_artifact_status(artifact)

    def increment_iteration(self) -> None:
        """Increment the iteration counter for auto-close functionality"""
        self._state_manager.increment_iteration()

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

    def set_events_queue(self, queue: Queue):
        self._events_queue = queue

    def get_dual_directory_fs(self):
        """Get the dual directory file system reference"""
        return self._dual_directory_fs
