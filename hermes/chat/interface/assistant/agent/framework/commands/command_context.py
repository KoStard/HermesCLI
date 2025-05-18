from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
    from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import Artifact
    from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode


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

    @property
    @abstractmethod
    def current_task_tree_node(self) -> "TaskTreeNode":
        """The current TaskTreeNode being processed."""
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
    def focus_down(self, subproblem_title: str) -> bool:
        """Initiate focusing down to a subproblem."""
        pass

    @abstractmethod
    def focus_up(self, message: str | None = None) -> bool:
        """Initiate focusing up to the parent problem, optionally with a message."""
        pass

    @abstractmethod
    def fail_and_focus_up(self, message: str | None = None) -> bool:
        """Mark the current problem as failed and initiate focusing up, optionally with a message."""
        pass

    @abstractmethod
    def search_artifacts(self, artifact_name: str) -> list[tuple["ResearchNode", "Artifact"]]:
        """Search for artifacts by name within the research project."""
        pass

    @abstractmethod
    def add_knowledge_entry(self, entry: Any) -> None:
        """Add an entry to the shared knowledge base."""
        pass
