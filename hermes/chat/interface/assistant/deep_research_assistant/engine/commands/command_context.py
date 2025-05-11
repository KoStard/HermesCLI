
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.engine import DeepResearchEngine
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import Research, ResearchNode


class CommandContext:
    """
    Context object for commands to access engine functionality without direct engine dependency.
    This improves separation of concerns and makes commands more testable.

    The CommandContext serves as a facade to the engine, providing commands with
    access to only the functionality they need while hiding implementation details.
    """

    def __init__(self, engine: 'DeepResearchEngine'):
        """
        Initialize the command context, optionally with a reference to the engine.

        Args:
            engine: Optional reference to the engine for initialization
        """
        # Reference to engine for special cases and callbacks
        self._engine = engine

    def refresh_from_engine(self):
        """Refresh context data from the engine"""
        pass

    @property
    def research(self) -> Research:
        return self._engine.research

    @property
    def current_node(self) -> ResearchNode:
        return self._engine.current_execution_state.active_node

    @property
    def children_queue(self):
        return self._engine.children_queue

    # Command output operations
    def add_command_output(self, command_name: str, args: dict, output: str) -> None:
        """Add command output to be included in the automatic response"""
        self._engine.add_command_output(command_name, args, output, self.current_node.get_title())

    # Log operations
    def add_to_permanent_log(self, content: str) -> None:
        """Add content to the permanent log"""
        if content:
            # Update permanent logs
            self._engine.research.get_permanent_logs().add_log(content)

    def focus_down(self, subproblem_title: str) -> bool:
        return self._engine.focus_down(subproblem_title)

    def focus_up(self, message: str | None = None) -> bool:
        # Pass the message to the engine's method
        return self._engine.focus_up(message=message)

    def fail_and_focus_up(self, message: str | None = None) -> bool:
        # Pass the message to the engine's method
        return self._engine.fail_and_focus_up(message=message)
