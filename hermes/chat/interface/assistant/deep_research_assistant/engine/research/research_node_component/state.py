import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition_manager import ProblemStatus

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode

@dataclass
class NodeState:
    """State of a research node, including open/closed artifacts and problem status"""
    artifacts_status: Dict[str, bool] = field(default_factory=dict)  # Using artifact names as keys for serialization
    problem_status: ProblemStatus = ProblemStatus.NOT_STARTED


class StateManager:
    """Manages the state for a research node"""

    def __init__(self, node: 'ResearchNode'):
        self.node = node
        self._state = NodeState()
        self._state_file_path = None
        if node.get_path():
            self._state_file_path = node.get_path() / "node_state.json"
            self.load()

    @classmethod
    def load_for_research_node(cls, research_node: 'ResearchNode') -> list["StateManager"]:
        """Load state manager for a research node"""
        manager = cls(research_node)
        return [manager]

    def get_state(self) -> NodeState:
        """Get the current state"""
        return self._state

    def set_artifact_status(self, artifact: Artifact, is_open: bool) -> None:
        """Set the status of an artifact"""
        self._state.artifacts_status[artifact.name] = is_open
        self.save()

    def get_artifact_status(self, artifact: Artifact) -> bool:
        """Get the status of an artifact"""
        return self._state.artifacts_status.get(artifact.name, True)  # Default to open if not found

    def set_problem_status(self, status: ProblemStatus) -> None:
        """Set the problem status"""
        self._state.problem_status = status
        self.save()

    def get_problem_status(self) -> ProblemStatus:
        """Get the problem status"""
        return self._state.problem_status

    def save(self) -> None:
        """Save state to file"""
        if not self._state_file_path:
            return

        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self._state_file_path), exist_ok=True)
            
            state_dict = {
                "artifacts_status": self._state.artifacts_status,
                "problem_status": self._state.problem_status.value
            }
            
            with open(self._state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving node state: {e}")

    def load(self) -> None:
        """Load state from file"""
        if not self._state_file_path or not os.path.exists(self._state_file_path):
            return

        try:
            with open(self._state_file_path, encoding='utf-8') as f:
                data = json.load(f)
                
            # Load artifact status
            self._state.artifacts_status = data.get("artifacts_status", {})
            
            # Load problem status
            status_value = data.get("problem_status", ProblemStatus.NOT_STARTED.value)
            try:
                self._state.problem_status = ProblemStatus(status_value)
            except ValueError:
                self._state.problem_status = ProblemStatus.NOT_STARTED
                
        except Exception as e:
            print(f"Error loading node state: {e}")
