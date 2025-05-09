from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.criteria import Criterion
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition import (
    ProblemDefinition,
)

from . import ResearchNode


class ResearchNodeImpl(ResearchNode):
    children: list[ResearchNode]
    artifacts: list[Artifact]
    criteria: list[Criterion]
    problem: ProblemDefinition

    def __init__(self, problem: ProblemDefinition) -> None:
        self.children = []
        self.artifacts = []
        self.criteria = []
        self.problem = problem

    def list_child_nodes(self) -> list[ResearchNode]:
        return self.children

    def add_child_node(self, child_node: ResearchNode):
        self.children.append(child_node)

    def get_artifacts(self) -> list[Artifact]:
        return self.artifacts

    def get_criteria(self) -> list[Criterion]:
        return self.criteria

    def get_problem(self) -> ProblemDefinition:
        return self.problem

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts.append(artifact)

    def add_criterion(self, criterion: Criterion) -> None:
        self.criteria.append(criterion)
