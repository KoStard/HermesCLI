from pathlib import Path

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import (
    Artifact,
    ArtifactManager,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.criteria import Criterion
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history.history import (
    ResearchNodeHistory,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.logger import ResearchNodeLogger
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition import (
    ProblemDefinition,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.state import NodeState, ProblemStatus

from . import ResearchNode


class ResearchNodeImpl(ResearchNode):
    def __init__(self, problem: ProblemDefinition, title: str, parent: 'ResearchNodeImpl | None', path: Path) -> None:
        self.children: list[ResearchNode] = []
        self.artifacts: list[Artifact] = []
        self.criteria: list[Criterion] = []
        self.problem: ProblemDefinition = problem
        self.title: str = title
        self.parent: ResearchNodeImpl | None = parent
        self._history: ResearchNodeHistory = ResearchNodeHistory()
        self._path: Path = path
        self._status: ProblemStatus = ProblemStatus.NOT_STARTED
        self._artifacts_status: dict[Artifact, bool] = {}

        # Component managers
        self.artifact_manager: ArtifactManager = ArtifactManager(self)
        self.logger: ResearchNodeLogger = ResearchNodeLogger(self)

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

        self.artifacts = self.artifact_manager.artifacts

    def list_child_nodes(self) -> list[ResearchNode]:
        return self.children

    def add_child_node(self, child_node: ResearchNode):
        self.children.append(child_node)
        self.save()

    def get_parent(self) -> ResearchNode | None:
        return self.parent

    def get_name(self) -> str:
        return self.title

    def get_artifacts(self) -> list[Artifact]:
        return self.artifacts

    def get_criteria(self) -> list[Criterion]:
        return self.criteria

    def get_criteria_met_count(self) -> int:
        count = 0
        for criterion in self.criteria:
            if criterion.is_completed:
                count += 1
        return count

    def get_criteria_total_count(self) -> int:
        return len(self.criteria)

    def get_problem(self) -> ProblemDefinition:
        return self.problem

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts.append(artifact)
        # Default to open status
        self._artifacts_status[artifact] = True

        # Save to disk if artifact manager is available
        if self.artifact_manager:
            self.artifact_manager.artifacts = self.artifacts
            self.artifact_manager.save()

    def add_criterion(self, criterion: Criterion) -> None:
        self.criteria.append(criterion)
        self.save()

    def get_title(self) -> str:
        return self.title

    def get_node_state(self) -> NodeState:
        return NodeState(
            artifacts_status=self._artifacts_status.copy(),
            problem_status=self._status
        )

    def set_problem_status(self, status: ProblemStatus):
        self._status = status
        self.save()

    def get_problem_status(self) -> ProblemStatus:
        return self._status

    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        if artifact in self._artifacts_status:
            self._artifacts_status[artifact] = is_open
            self.save()

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

    def save(self):
        """Save the node data to disk"""
        if not self._path:
            return

        # Save problem definition with metadata
        problem_def_path = self._path / "Problem Definition.md"

        md_file = MarkdownFileWithMetadataImpl(self.title, self.problem.content)
        md_file.add_property("status", self._status.value)
        md_file.save_file(str(problem_def_path))

        # Save criteria
        criteria_path = self._path / "Criteria of Definition of Done.md"
        with open(criteria_path, "w", encoding="utf-8") as f:
            for i, criterion in enumerate(self.criteria):
                status = "[x]" if criterion.is_completed else "[ ]"
                f.write(f"{i + 1}. {status} {criterion.content}\n")

        # Save artifacts using artifact manager
        if self.artifact_manager:
            self.artifact_manager.save()

        # Save each child node
        for child in self.children:
            if isinstance(child, ResearchNodeImpl) and child.get_path():
                child.save()
