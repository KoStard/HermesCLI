from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from hermes.chat.interface.assistant.framework.commands import CommandContext

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.deep_research.research import Research, ResearchNode
    from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact
    from hermes.chat.interface.assistant.deep_research.task_processor import TaskProcessor


class ResearchCommandContext(CommandContext, ABC):
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


ResearchCommandContextType = TypeVar("ResearchCommandContextType", bound=ResearchCommandContext)


class ResearchCommandContextFactory(ABC, Generic[ResearchCommandContextType]):
    @abstractmethod
    def create_command_context(
        self, task_processor: "TaskProcessor", current_node: "ResearchNode", command_processor: "CommandProcessor"
    ) -> ResearchCommandContextType:
        pass

from .commands import register_deep_research_commands
