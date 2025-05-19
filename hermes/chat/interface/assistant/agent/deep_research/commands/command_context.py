from typing import TYPE_CHECKING, Any

from hermes.chat.interface.assistant.agent.framework.commands.command_context import CommandContext
from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import Artifact

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor
    from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode


class CommandContextImpl(CommandContext):
    """
    Concrete implementation of CommandContext for Deep Research commands.
    Provides commands with access to necessary components via the TaskProcessor.
    """

    def __init__(self, task_processor: "TaskProcessor", current_task_tree_node: "TaskTreeNode", command_processor: "CommandProcessor"):
        self._task_processor = task_processor
        self._command_processor = command_processor
        self._current_task_tree_node = current_task_tree_node
        self._current_node = current_task_tree_node.get_research_node()

    @property
    def current_node(self) -> "ResearchNode":
        return self._current_node

    @property
    def research_project(self) -> "Research":
        return self._task_processor.research_project

    @property
    def current_task_tree_node(self) -> "TaskTreeNode":
        return self._current_task_tree_node

    def add_command_output(self, command_name: str, args: dict, output: str) -> None:
        """Add command output to the current node's auto-reply aggregator."""
        self._task_processor.add_command_output_to_auto_reply(command_name, args, output, self._current_task_tree_node)

    def add_to_permanent_log(self, content: str) -> None:
        if content:
            self.research_project.get_permanent_logs().add_log(content)

    def focus_down(self, subproblem_title: str) -> bool:
        # Delegate to CommandProcessor, which now resides within TaskProcessor
        return self._command_processor.focus_down(subproblem_title, self._current_task_tree_node)

    def focus_up(self, message: str | None = None) -> bool:
        return self._command_processor.focus_up(message, self._current_task_tree_node)

    def fail_and_focus_up(self, message: str | None = None) -> bool:
        return self._command_processor.fail_and_focus_up(message, self._current_task_tree_node)

    def search_artifacts(self, artifact_name: str) -> list[tuple["ResearchNode", "Artifact"]]:
        return self.research_project.search_artifacts(artifact_name)

    def add_knowledge_entry(self, entry: Any) -> None:
        self.research_project.get_knowledge_base().add_entry(entry)
