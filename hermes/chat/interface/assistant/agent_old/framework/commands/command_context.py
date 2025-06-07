from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent_old.framework.research import Research, ResearchNode
    from hermes.chat.interface.assistant.agent_old.framework.research.research_node_component.artifact import Artifact


class CommandContext(ABC):
    """
    Abstract base class for command execution context.
    Provides an interface for commands to interact with the agent's framework
    without direct dependencies on concrete engine or processor classes.
    """

    @property
    @abstractmethod
    def current_node(self) -> "ResearchNode":
        """The current ResearchNode being processed."""
        pass

    @property
    @abstractmethod
    def research_project(self) -> "Research":
        """The overall Research project instance."""
        pass

    @abstractmethod
    def add_command_output(self, command_name: str, args: dict, output: str) -> None:
        """Add command output to be included in the automatic response for the current node."""
        pass

    @abstractmethod
    def add_to_permanent_log(self, content: str) -> None:
        """Add content to the research project's permanent log."""
        pass

    @abstractmethod
    def activate_subtask(self, subproblem_title: str) -> bool:
        pass

    @abstractmethod
    def wait_for_subtask(self, subproblem_title: str):
        pass

    @abstractmethod
    def finish_node(self, message: str | None = None) -> bool:
        pass

    @abstractmethod
    def fail_node(self, message: str | None = None) -> bool:
        pass

    @abstractmethod
    def search_artifacts(self, artifact_name: str) -> list[tuple["ResearchNode", "Artifact"]]:
        """Search for artifacts by name within the research project."""
        pass

    @abstractmethod
    def add_knowledge_entry(self, entry: Any) -> None:
        """Add an entry to the shared knowledge base."""
        pass
