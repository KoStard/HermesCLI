from abc import ABC, abstractmethod
from enum import Enum

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact


class ProblemStatus(Enum):
    NOT_STARTED = "NOT_STARTED"  # Problem has not been started yet
    PENDING = "PENDING"  # Problem is temporarily paused (focus moved to child)
    IN_PROGRESS = "IN_PROGRESS"  # Problem is currently being worked on
    FINISHED = "FINISHED"  # Problem has been successfully completed
    FAILED = "FAILED"  # Problem could not be solved
    CANCELLED = "CANCELLED"  # Problem was determined to be unnecessary


class NodeState(ABC):
    @abstractmethod
    def get_artifacts_status(self) -> dict[Artifact, bool]:
        pass

    @abstractmethod
    def open_artifact(self, artifact: Artifact):
        pass

    @abstractmethod
    def close_artifact(self, artifact: Artifact):
        pass

    @abstractmethod
    def get_progress_status(self) -> ProblemStatus:
        pass
