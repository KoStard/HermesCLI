from pathlib import Path

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.frontmatter_manager import FrontmatterManager
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import (
    Artifact,
    ArtifactManager,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.criteria import Criterion
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history import ResearchNodeHistory
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.logger import ResearchNodeLogger
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition import (
    ProblemDefinition,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.state import NodeState, ProblemStatus

from . import ResearchNode


class ResearchNodeImpl(ResearchNode):
    def __init__(self, problem: ProblemDefinition, title: str, parent: 'ResearchNodeImpl' = None) -> None:
        self.children: list[ResearchNode] = []
        self.artifacts: list[Artifact] = []
        self.criteria: list[Criterion] = []
        self.problem: ProblemDefinition = problem
        self.title: str = title
        self.parent: ResearchNodeImpl | None = parent
        self._history: ResearchNodeHistory = ResearchNodeHistory()
        self._path: Path | None = None
        self._status: ProblemStatus = ProblemStatus.NOT_STARTED
        self._artifacts_status: dict[Artifact, bool] = {}

        # Component managers
        self.artifact_manager: ArtifactManager | None = None
        self.logger: ResearchNodeLogger | None = None

        # Initialize file system components if path is set
        self._init_components()

    def _init_components(self):
        """Initialize node components"""
        # Create artifact manager
        self.artifact_manager = ArtifactManager(self)

        # Create logger
        self.logger = ResearchNodeLogger(self)

        # Load initial artifacts if available
        if self.artifact_manager is not None:
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

    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        if artifact in self._artifacts_status:
            self._artifacts_status[artifact] = is_open
            self.save()

    def get_history(self) -> ResearchNodeHistory:
        return self._history

    def get_path(self) -> Path | None:
        return self._path

    def set_path(self, path: Path):
        self._path = path

        # Create necessary directories
        if path and not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        # Create the standard structure
        if path:
            # Create artifacts directory
            artifacts_dir = path / "Artifacts"
            artifacts_dir.mkdir(exist_ok=True)

            # Create subproblems directory
            subproblems_dir = path / "Subproblems"
            subproblems_dir.mkdir(exist_ok=True)

            # Create logs directory
            logs_dir = path / "logs_and_debug"
            logs_dir.mkdir(exist_ok=True)

        # Re-init components with new path
        self._init_components()

        # Save node data to disk
        self.save()

    def save(self):
        """Save the node data to disk"""
        if not self._path:
            return

        # Save problem definition with frontmatter
        problem_def_path = self._path / "Problem Definition.md"
        frontmatter = {"title": self.title, "status": self._status.value}

        frontmatter_manager = FrontmatterManager()
        content = frontmatter_manager.add_frontmatter(self.problem.content, frontmatter)

        with open(problem_def_path, "w", encoding="utf-8") as f:
            f.write(content)

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
