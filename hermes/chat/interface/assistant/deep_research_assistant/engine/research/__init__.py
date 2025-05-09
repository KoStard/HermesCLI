from abc import ABC, abstractmethod
from typing import TypeVar

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.criteria import Criterion
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition import (
    ProblemDefinition,
)

N = TypeVar('N', bound='ResearchNode')

class ResearchNode(ABC):
    @abstractmethod
    def list_child_nodes(self: N) -> list[N]:
        pass

    @abstractmethod
    def add_child_node(self, child_node: 'ResearchNode'):
        pass

    @abstractmethod
    def get_parent(self) -> 'ResearchNode | None':
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_artifacts(self) -> list[Artifact]:
        pass

    @abstractmethod
    def get_criteria(self) -> list[Criterion]:
        pass

    @abstractmethod
    def get_problem(self) -> ProblemDefinition:
        pass

    @abstractmethod
    def add_artifact(self, artifact: Artifact) -> None:
        pass

    @abstractmethod
    def add_criterion(self, criterion: Criterion) -> None:
        pass


class Research(ABC):
    @abstractmethod
    def research_already_exists(self):
        pass

    @abstractmethod
    def create_research(self) -> ResearchNode:
        pass

    @abstractmethod
    def load_existing_research(self) -> ResearchNode:
        pass

    @abstractmethod
    def get_root_node(self) -> ResearchNode:
        pass
