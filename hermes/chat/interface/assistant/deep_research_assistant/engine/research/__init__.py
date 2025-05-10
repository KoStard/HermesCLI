from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.criteria import Criterion
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history.history import (
    ResearchNodeHistory,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.logger import ResearchNodeLogger
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition import (
    ProblemDefinition,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.state import NodeState, ProblemStatus
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_project_component.knowledge_base import KnowledgeBase
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_project_component.permanent_log import (
    NodePermanentLogs,
)

N = TypeVar('N', bound='ResearchNode')

class ResearchNode(ABC):
    # Should automatically handle file updates
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
    def get_criteria_met_count(self) -> int:
        pass

    @abstractmethod
    def get_criteria_total_count(self) -> int:
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

    @abstractmethod
    def get_title(self) -> str:
        pass

    @abstractmethod
    def get_node_state(self) -> NodeState:
        pass

    @abstractmethod
    def set_problem_status(self, status: ProblemStatus):
        pass

    @abstractmethod
    def get_problem_status(self) -> ProblemStatus:
        pass

    @abstractmethod
    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        pass

    @abstractmethod
    def get_history(self) -> ResearchNodeHistory:
        pass

    @abstractmethod
    def get_path(self) -> Path:
        pass

    @abstractmethod
    def get_logger(self) -> ResearchNodeLogger:
        pass

class Research(ABC):
    @abstractmethod
    def research_already_exists(self) -> bool:
        pass

    @abstractmethod
    def research_initiated(self) -> bool:
        # Return true if research has been loaded or created already
        pass

    @abstractmethod
    def initiate_research(self, root_node: ResearchNode):
        pass

    @abstractmethod
    def load_existing_research(self):
        pass

    @abstractmethod
    def get_root_node(self) -> ResearchNode:
        pass

    @abstractmethod
    def get_permanent_logs(self) -> NodePermanentLogs:
        pass

    @abstractmethod
    def get_knowledge_base(self) -> KnowledgeBase:
        pass
