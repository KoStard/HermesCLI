from pathlib import Path

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import (
    Artifact,
    ArtifactManager,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.criteria_manager import (
    CriteriaManager,
    Criterion,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history.history import (
    ResearchNodeHistory,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.logger import ResearchNodeLogger
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemDefinitionManager,
    ProblemStatus,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.state import NodeState

from . import ResearchNode


class ResearchNodeImpl(ResearchNode):
    def __init__(self, problem: ProblemDefinition, title: str, parent: 'ResearchNode | None', path: Path) -> None:
        self.children: list[ResearchNode] = []
        self.parent: ResearchNode | None = parent
        self._history: ResearchNodeHistory = ResearchNodeHistory()
        self._path: Path = path
        self._artifacts_status: dict[Artifact, bool] = {}
        self._title = title

        # Component managers
        self.artifact_manager: ArtifactManager = ArtifactManager(self)
        self.criteria_manager: CriteriaManager = CriteriaManager(self)
        self.logger: ResearchNodeLogger = ResearchNodeLogger(self)
        self.problem_manager: ProblemDefinitionManager = ProblemDefinitionManager(self, problem, ProblemStatus.NOT_STARTED)

        # Initialize file system components if path is set
        self._init_components()

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

        # Load criteria
        self.criteria_manager = CriteriaManager.load_for_research_node(self)[0]

    def list_child_nodes(self) -> list[ResearchNode]:
        return self.children

    def add_child_node(self, child_node: ResearchNode):
        self.children.append(child_node)
        # Each child node manages its own saving through its components

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
        # Default to open status
        self._artifacts_status[artifact] = True

        # Add to artifact manager and save
        self.artifact_manager.artifacts.append(artifact)
        self.artifact_manager.save()

    def add_criterion(self, criterion: Criterion):
        """
        Add a criterion and return its index
        If the criterion already exists, return its index
        """
        self.criteria_manager.add_criterion(criterion)

    def get_title(self) -> str:
        return self._title

    def get_node_state(self) -> NodeState:
        return NodeState(
            artifacts_status=self._artifacts_status.copy(),
            problem_status=self.problem_manager.status
        )

    def set_problem_status(self, status: ProblemStatus):
        self.problem_manager.update_status(status)

    def get_problem_status(self) -> ProblemStatus:
        return self.problem_manager.status

    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        if artifact in self._artifacts_status:
            self._artifacts_status[artifact] = is_open
            # No save needed as this is just in-memory state

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
