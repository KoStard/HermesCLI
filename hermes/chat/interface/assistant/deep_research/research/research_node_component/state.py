import json
import os
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.deep_research.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode

# Auto-close settings
ARTIFACT_AUTO_CLOSE_ITERATIONS = 5  # Number of message iterations before auto-close


@dataclass
class NodeState:
    """State of a research node, including open/closed artifacts and problem status"""

    id: str | None = None
    artifacts_status: dict[str, bool] = field(default_factory=dict)  # Using artifact names as keys for serialization
    artifacts_open_iterations: dict[str, int] = field(default_factory=dict)  # Track iteration when artifacts were opened
    current_iteration: int = 0  # Track current message iteration count
    problem_status: ProblemStatus = ProblemStatus.CREATED
    resolution_message: str | None = None
    pending_child_node_ids: set[str] = field(default_factory=set)


class StateManager:
    """Manages the state for a research node"""

    def __init__(self, node: "ResearchNode"):
        self.node = node
        self._state_file_path = node.get_path() / "node_state.json"
        self._state = NodeState()
        self.load()
        if not self._state.id:
            self._state.id = str(hash(self._state_file_path))

    @classmethod
    def load_for_research_node(cls, research_node: "ResearchNode") -> list["StateManager"]:
        """Load state manager for a research node"""
        manager = cls(research_node)
        return [manager]

    def get_id(self) -> str:
        assert self._state.id
        return self._state.id

    def get_state(self) -> NodeState:
        """Get the current state"""
        return replace(self._state)

    def set_artifact_status(self, artifact: Artifact, is_open: bool) -> None:
        """Set the status of an artifact"""
        self._state.artifacts_status[artifact.name] = is_open

        if is_open:
            # Track which iteration the artifact was opened for auto-close functionality
            self._state.artifacts_open_iterations[artifact.name] = self._state.current_iteration
        else:
            # Remove iteration tracking when manually closed
            self._state.artifacts_open_iterations.pop(artifact.name, None)

        self.save()

    def get_artifact_status(self, artifact: Artifact) -> bool:
        """Get the status of an artifact, checking for auto-close"""
        # Check if artifact should be auto-closed
        self._check_auto_close_artifact(artifact.name)
        return self._state.artifacts_status.get(artifact.name, False)  # Default to closed if not found

    def _check_auto_close_artifact(self, artifact_name: str) -> None:
        """Check if an artifact should be auto-closed based on iteration count"""
        if artifact_name not in self._state.artifacts_status:
            return

        # Only check artifacts that are currently open
        if not self._state.artifacts_status.get(artifact_name, False):
            return

        # Get the iteration when the artifact was opened
        open_iteration = self._state.artifacts_open_iterations.get(artifact_name)
        if open_iteration is None:
            return

        # Check if enough iterations have passed to auto-close
        iterations_passed = self._state.current_iteration - open_iteration
        if iterations_passed >= ARTIFACT_AUTO_CLOSE_ITERATIONS:
            # Auto-close the artifact
            self._state.artifacts_status[artifact_name] = False
            self._state.artifacts_open_iterations.pop(artifact_name, None)
            self.save()

    def set_problem_status(self, status: ProblemStatus) -> None:
        """Set the problem status"""
        self._state.problem_status = status

        if status in [ProblemStatus.CREATED, ProblemStatus.READY_TO_START, ProblemStatus.IN_PROGRESS]:
            self._state.resolution_message = None
        self.save()

    def get_problem_status(self) -> ProblemStatus:
        """Get the problem status"""
        return self._state.problem_status

    def add_child_node_to_wait(self, child_node: "ResearchNode"):
        self._state.pending_child_node_ids.add(child_node.get_id())

    def remove_child_node_to_wait(self, child_node: "ResearchNode") -> bool:
        node_id = child_node.get_id()
        if node_id in self._state.pending_child_node_ids:
            self._state.pending_child_node_ids.remove(node_id)
            return True
        return False

    def set_resolution_message(self, message: str | None) -> None:
        """Set the resolution message and save"""
        print("Setting resolution message", message)
        self._state.resolution_message = message
        self.save()

    def get_resolution_message(self) -> str | None:
        """Get the resolution message"""
        return self._state.resolution_message

    def increment_iteration(self) -> None:
        """Increment the current iteration counter"""
        self._state.current_iteration += 1
        self.save()

    def save(self) -> None:
        """Save state to file"""
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self._state_file_path), exist_ok=True)

            state_dict = {
                "artifacts_status": self._state.artifacts_status,
                "artifacts_open_iterations": self._state.artifacts_open_iterations,
                "current_iteration": self._state.current_iteration,
                "problem_status": self._state.problem_status.value,
                "resolution_message": self._state.resolution_message,
                "pending_child_node_ids": list(self._state.pending_child_node_ids),
            }

            with open(self._state_file_path, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving node state: {e}")

    def load(self) -> None:
        """Load state from file"""
        if not os.path.exists(self._state_file_path):
            return

        try:
            with open(self._state_file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Load artifact status and iteration tracking
            self._state.artifacts_status = data.get("artifacts_status", {})
            self._state.artifacts_open_iterations = data.get("artifacts_open_iterations", {})
            self._state.current_iteration = data.get("current_iteration", 0)

            # Load problem status
            status_value = data.get("problem_status", ProblemStatus.CREATED.value)

            try:
                problem_status = ProblemStatus(status_value)
            except ValueError:
                problem_status = ProblemStatus.CREATED

            # If was interrupted while in progress, we consider it to be failed.
            if problem_status == ProblemStatus.IN_PROGRESS:
                problem_status = ProblemStatus.FAILED

            self._state.problem_status = problem_status

            self._state.resolution_message = data.get("resolution_message")
            self._state.pending_child_node_ids = set(data.get("pending_child_node_ids"))

        except Exception as e:
            print(f"Error loading node state: {e}")
