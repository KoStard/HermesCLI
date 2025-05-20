from typing import TYPE_CHECKING, Any

from hermes.chat.interface.assistant.agent.framework.commands.command_context import CommandContext
from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import Artifact

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor


class CommandContextImpl(CommandContext):
    """
    Concrete implementation of CommandContext for Deep Research commands.
    Provides commands with access to necessary components via the TaskProcessor.
    """

    def __init__(self, task_processor: "TaskProcessor", command_processor: "CommandProcessor", current_node: ResearchNode):
        self._task_processor = task_processor
        self._command_processor = command_processor
        self._current_node = current_node

    @property
    def current_node(self) -> "ResearchNode":
        return self._current_node

    @property
    def research_project(self) -> "Research":
        return self._task_processor.research_project

    def add_command_output(self, command_name: str, args: dict, output: str) -> None:
        """Add command output to the current node's auto-reply aggregator."""
        self._task_processor.add_command_output_to_auto_reply(command_name, args, output, self.current_node)

    def add_to_permanent_log(self, content: str) -> None:
        if content:
            self.research_project.get_permanent_logs().add_log(content)

    def activate_subtask(self, subproblem_title: str) -> bool:
        # Delegate to CommandProcessor, which now resides within TaskProcessor
        return self._command_processor.activate_subtask(subproblem_title, self.current_node)

    def wait_for_subtask(self, subproblem_title: str):
        self._command_processor.wait_for_subtask(subproblem_title, self.current_node)

    def finish_node(self, message: str | None = None) -> bool:
        return self._command_processor.finish_node(message, self.current_node)

    def fail_node(self, message: str | None = None) -> bool:
        return self._command_processor.fail_node(message, self.current_node)

    def search_artifacts(self, artifact_name: str) -> list[tuple["ResearchNode", "Artifact"]]:
        return self.research_project.search_artifacts(artifact_name)

    def add_knowledge_entry(self, entry: Any) -> None:
        self.research_project.get_knowledge_base().add_entry(entry)
