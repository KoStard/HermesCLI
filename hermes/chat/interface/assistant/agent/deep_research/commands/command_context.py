
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent.framework.commands.command_context import CommandContext

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.engine import AgentEngine
    from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode


class CommandContextImpl(CommandContext):
    """
    Context object for commands to access engine functionality without direct engine dependency.
    This improves separation of concerns and makes commands more testable.

    The CommandContext serves as a facade to the engine, providing commands with
    access to only the functionality they need while hiding implementation details.
    """

    def __init__(self, engine: 'AgentEngine', current_state_machine_node: 'TaskTreeNode'):
        """
        Initialize the command context, optionally with a reference to the engine.

        Args:
            engine: Optional reference to the engine for initialization
            current_node: The current state machine node
        """
        # Reference to engine for special cases and callbacks
        self._engine = engine
        self.current_state_machine_node = current_state_machine_node
        self.current_node = current_state_machine_node.get_research_node()


    # Command output operations
    def add_command_output(self, command_name: str, args: dict, output: str) -> None:
        """Add command output to be included in the automatic response"""
        self._engine.add_command_output(command_name, args, output, self.current_node.get_title(), self.current_state_machine_node)

    # Log operations
    def add_to_permanent_log(self, content: str) -> None:
        """Add content to the permanent log"""
        if content:
            # Update permanent logs
            self._engine.research.get_permanent_logs().add_log(content)

    def focus_down(self, subproblem_title: str) -> bool:
        return self._engine.focus_down(subproblem_title, self.current_state_machine_node)

    def focus_up(self, message: str | None = None) -> bool:
        # Pass the message and current node to the engine's method
        return self._engine.focus_up(message=message, current_state_machine_node=self.current_state_machine_node)

    def fail_and_focus_up(self, message: str | None = None) -> bool:
        # Pass the message and current node to the engine's method
        return self._engine.fail_and_focus_up(message=message, current_state_machine_node=self.current_state_machine_node)

    def search_artifacts(self, artifact_name: str):
        """Search for artifacts by name in the research."""
        return self._engine.research.search_artifacts(artifact_name)

    def add_knowledge_entry(self, entry) -> None:
        """Add a knowledge entry to the shared knowledge base."""
        self._engine.research.get_knowledge_base().add_entry(entry)
