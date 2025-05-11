from dataclasses import dataclass
from enum import Enum

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact


class ProblemStatus(Enum):
    NOT_STARTED = "NOT_STARTED"  # Problem has not been started yet
    PENDING = "PENDING"  # Problem is temporarily paused (focus moved to child)
    IN_PROGRESS = "IN_PROGRESS"  # Problem is currently being worked on
    FINISHED = "FINISHED"  # Problem has been successfully completed
    FAILED = "FAILED"  # Problem could not be solved
    CANCELLED = "CANCELLED"  # Problem was determined to be unnecessary


@dataclass(frozen=True)
class NodeState:
    artifacts_status: dict[Artifact, bool]
    problem_status: ProblemStatus
