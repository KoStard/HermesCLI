from pathlib import Path

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.criteria import Criterion
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history import ResearchNodeHistory
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
        self.parent: 'ResearchNodeImpl' = parent
        self._history: ResearchNodeHistory = ResearchNodeHistory()
        self._path: Path = None
        self._status: ProblemStatus = ProblemStatus.NOT_STARTED
        self._artifacts_status: dict[Artifact, bool] = {}

    def list_child_nodes(self) -> list[ResearchNode]:
        return self.children

    def add_child_node(self, child_node: ResearchNode):
        self.children.append(child_node)

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

    def add_criterion(self, criterion: Criterion) -> None:
        self.criteria.append(criterion)

    def get_title(self) -> str:
        return self.title

    def get_node_state(self) -> NodeState:
        return NodeState(
            artifacts_status=self._artifacts_status.copy(),
            problem_status=self._status
        )

    def set_problem_status(self, status: ProblemStatus):
        self._status = status

    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        if artifact in self._artifacts_status:
            self._artifacts_status[artifact] = is_open

    def get_history(self) -> ResearchNodeHistory:
        return self._history
    
    def get_path(self) -> Path:
        return self._path
    
    def set_path(self, path: Path):
        self._path = path
