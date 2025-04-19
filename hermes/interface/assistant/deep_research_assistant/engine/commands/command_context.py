from typing import Dict
from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import FileSystem
from hermes.interface.assistant.deep_research_assistant.engine.context.history import ChatHistory


class CommandContext:
    """
    Context object for commands to access engine functionality without direct engine dependency.
    This improves separation of concerns and makes commands more testable.

    The CommandContext serves as a facade to the engine, providing commands with
    access to only the functionality they need while hiding implementation details.
    """

    def __init__(self, engine=None):
        """
        Initialize the command context, optionally with a reference to the engine.

        Args:
            engine: Optional reference to the engine for initialization
        """
        # Reference to engine for special cases and callbacks
        self._engine = engine

        self.file_system = engine.file_system
        self.chat_history = engine.chat_history
        self._permanent_log = engine.permanent_log

    def refresh_from_engine(self):
        """Refresh context data from the engine"""
        pass

    @property
    def current_node(self):
        return self._engine.current_node

    @property
    def finished(self):
        return self._engine.finished

    @property
    def children_queue(self):
        return self._engine.children_queue

    # File system operations
    def set_file_system(self, file_system: FileSystem) -> None:
        """
        Set the file system reference

        Args:
            file_system: The file system to use
        """
        self.file_system = file_system

    def update_files(self) -> None:
        """
        Update files in the file system
        """
        self.file_system.update_files()

    # Command output operations
    def add_command_output(self, command_name: str, args: Dict, output: str) -> None:
        """Add command output to be included in the automatic response"""
        self._engine.add_command_output(
            command_name, args, output, self.current_node.title
        )

    # Log operations
    def add_to_permanent_log(self, content: str) -> None:
        """Add content to the permanent log"""
        if content:
            # Update engine if available
            self._engine.permanent_log.append(content)

    def is_problem_defined(self) -> bool:
        """Check if the problem is defined"""
        return self._engine.is_root_problem_defined()

    # Execution state operations
    def set_finished(self, finished: bool) -> None:
        """Set whether execution is finished"""
        self._finished = finished
        # Update engine if available
        self._engine.finished = finished

    def is_finished(self) -> bool:
        """Check if execution is finished"""
        return self._finished

    # Chat history operations
    def set_chat_history(self, chat_history: ChatHistory) -> None:
        """
        Set the chat history reference

        Args:
            chat_history: The chat history to use
        """
        self.chat_history = chat_history

    def focus_down(self, subproblem_title: str) -> bool:
        return self._engine.focus_down(subproblem_title)

    def focus_up(self) -> bool:
        return self._engine.focus_up()

    def fail_and_focus_up(self) -> bool:
        return self._engine.fail_and_focus_up()
