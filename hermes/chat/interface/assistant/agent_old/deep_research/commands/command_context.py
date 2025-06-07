from typing import TYPE_CHECKING, Any

from hermes.chat.interface.assistant.agent_old.framework.commands.command_context import CommandContext
from hermes.chat.interface.assistant.agent_old.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent_old.framework.research.research_node_component.artifact import Artifact

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent_old.framework.command_processor import CommandProcessor
    from hermes.chat.interface.assistant.agent_old.framework.task_processor import TaskProcessor


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
        # First search in current research
        results = self.research_project.search_artifacts(artifact_name)

        # If using repo structure, also search in sibling research instances
        if hasattr(self.research_project, "search_artifacts_including_siblings"):
            # Get results from all research instances
            all_results = self.research_project.search_artifacts_including_siblings(artifact_name)

            # Filter to only include results from current research
            current_research_name = None
            for name, node, artifact in all_results:
                # Find current research name
                if any((n, a) == (node, artifact) for n, a in results):
                    current_research_name = name
                    break

            # Return results from current research
            return results

        return results

    def search_all_research_artifacts(self, artifact_name: str) -> list[tuple[str, "ResearchNode", "Artifact"]]:
        """
        Search for artifacts across all research instances (when using repo structure).

        Returns:
            List of (research_name, node, artifact) tuples
        """
        if hasattr(self.research_project, "search_artifacts_including_siblings"):
            return self.research_project.search_artifacts_including_siblings(artifact_name)
        else:
            # Fallback to current research only
            return [("current", node, artifact) for node, artifact in self.research_project.search_artifacts(artifact_name)]

    def add_knowledge_entry(self, entry: Any) -> None:
        self.research_project.get_knowledge_base().add_entry(entry)
