from abc import ABC, abstractmethod
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING, TypeVar

from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact, ArtifactManager
from hermes.chat.interface.assistant.deep_research.research.research_node_component.criteria_manager import Criterion
from hermes.chat.interface.assistant.deep_research.research.research_node_component.history.history import (
    ResearchNodeHistory,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_component.logger import ResearchNodeLogger
from hermes.chat.interface.assistant.deep_research.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemStatus,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_component.state import (
    NodeState,
)
from hermes.chat.interface.assistant.deep_research.research.research_project_component.external_file import (
    ExternalFilesManager,
)
from hermes.chat.interface.assistant.deep_research.research.research_project_component.knowledge_base import KnowledgeBase
from hermes.chat.interface.assistant.deep_research.research.research_project_component.permanent_log import NodePermanentLogs

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research.file_system.dual_directory_file_system import DualDirectoryFileSystem
    from hermes.chat.interface.assistant.deep_research.research.repo import Repo
    from hermes.chat.interface.assistant.deep_research.task_tree import TaskTree

N = TypeVar("N", bound="ResearchNode")


class ResearchNodeStatusChangeEvent:
    pass


class ResearchNode(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def list_child_nodes(self: N) -> list[N]:
        pass

    @abstractmethod
    def add_child_node(self, child_node: "ResearchNode"):
        pass

    @abstractmethod
    def get_parent(self) -> "ResearchNode | None":
        pass

    @abstractmethod
    def get_artifact_manager(self) -> "ArtifactManager":
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
    def append_to_problem_definition(self, content: str):
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
    def add_child_node_to_wait(self, child_node: "ResearchNode"):
        pass

    @abstractmethod
    def remove_child_node_to_wait(self, child_node: "ResearchNode"):
        pass

    @abstractmethod
    def set_resolution_message(self, message: str | None) -> None:
        pass

    @abstractmethod
    def set_artifact_status(self, artifact: Artifact, is_open: bool):
        pass

    @abstractmethod
    def get_artifact_status(self, artifact: Artifact) -> bool:
        pass

    @abstractmethod
    def increment_iteration(self) -> None:
        """Increment the iteration counter for auto-close functionality"""

    @abstractmethod
    def get_history(self) -> ResearchNodeHistory:
        pass

    @abstractmethod
    def get_path(self) -> Path:
        pass

    @abstractmethod
    def get_logger(self) -> ResearchNodeLogger:
        pass

    @abstractmethod
    def get_depth_from_root(self) -> int:
        pass

    @abstractmethod
    def create_child_node(self, title: str, problem_content: str) -> "ResearchNode":
        """Create a new child node for this research node.

        Args:
            title: Title of the child node
            problem_content: Content for the child node's problem definition

        Returns:
            The newly created child node
        """

    @abstractmethod
    def get_resolution_message(self) -> str | None:
        pass

    @abstractmethod
    def set_events_queue(self, queue: Queue):
        pass


class Research(ABC):
    @abstractmethod
    def research_already_exists(self) -> bool:
        pass

    @abstractmethod
    def has_root_problem_defined(self) -> bool:
        # Return true if the root problem has been defined (either created or loaded)
        pass

    @abstractmethod
    def initiate_research(self, root_node: ResearchNode):
        pass

    @abstractmethod
    def load_existing_research(self, task_tree: "TaskTree"):
        pass

    @abstractmethod
    def get_root_node(self) -> ResearchNode:
        pass

    @abstractmethod
    def get_root_directory(self) -> Path:
        pass

    @abstractmethod
    def get_permanent_logs(self) -> NodePermanentLogs:
        pass

    @abstractmethod
    def get_knowledge_base(self) -> KnowledgeBase:
        pass

    @abstractmethod
    def get_external_file_manager(self) -> ExternalFilesManager:
        pass

    @abstractmethod
    def search_artifacts(self, name: str) -> list[tuple[ResearchNode, Artifact]]:
        pass

    @abstractmethod
    def search_root_artifacts_from_specific_research(self, name: str, research_name: str) -> list[tuple[str, ResearchNode, Artifact]]:
        """Search for root-level artifacts from a specific research instance.

        Args:
            name: The artifact name to search for
            research_name: The specific research instance to search in

        Returns:
            List of (research_name, node, artifact) tuples where node is the root node
        """

    @abstractmethod
    def get_repo(self) -> "Repo | None":
        pass

    @abstractmethod
    def get_dual_directory_fs(self) -> "DualDirectoryFileSystem":
        pass
