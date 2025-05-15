from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

# Define a TypeVar representing any context type the specific interface might use
ContextType = TypeVar("ContextType")


class CommandSection:
    """Represents a section in a command (e.g., ///title, ///content)"""

    def __init__(
        self,
        name: str,
        required: bool = True,
        help_text: str = "",
        allow_multiple: bool = False,
    ):
        self.name = name
        self.required = required
        self.help_text = help_text
        self.allow_multiple = allow_multiple


# Make the Command class Generic, parameterized by the ContextType
class Command(ABC, Generic[ContextType]):
    """
    Base class for all commands, generic over the execution context.

    Specific command implementations should inherit from this class,
    specifying the concrete context type they expect (e.g., Command[MySpecificContext]).
    """

    def __init__(
        self,
        name: str,
        help_text: str = "",
    ):
        self.name = name
        self.help_text = help_text
        self.sections: list[CommandSection] = []

    def add_section(
        self,
        name: str,
        required: bool = True,
        help_text: str = "",
        allow_multiple: bool = False,
    ) -> None:
        """Add a section definition to this command"""
        self.sections.append(CommandSection(name, required, help_text, allow_multiple=allow_multiple))

    def get_required_sections(self) -> list[str]:
        """Get names of all required sections"""
        return [section.name for section in self.sections if section.required]

    def get_all_sections(self) -> list[str]:
        """Get names of all sections"""
        return [section.name for section in self.sections]

    def get_section_help(self, section_name: str) -> str:
        """Get help text for a specific section"""
        for section in self.sections:
            if section.name == section_name:
                return section.help_text
        return ""

    @abstractmethod
    def execute(self, context: ContextType, args: dict[str, Any]):
        """
        Execute the command with the given arguments and a context object
        provided by the calling interface.

        Args:
            context: The context object specific to the calling interface.
            args: A dictionary containing the parsed arguments for the command,
                  where keys are section names and values are the section content
                  (or a list of contents if allow_multiple=True).

        Returns:
            Generator of events produced by command execution.
        """
        pass

    def validate(self, args: dict[str, Any]) -> list[str]:
        """
        Validate command arguments against defined sections.
        Returns a list of error messages.
        """
        errors = []
        for section in self.sections:
            if section.required and section.name not in args:
                errors.append(f"Missing required section '{section.name}'")
        # Basic validation is done here, more specific validation can be added
        # by overriding this method in subclasses.
        return errors

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Transform arguments before validation or execution if needed.
        Default implementation returns args unchanged.
        """
        return args

    def should_be_last_in_message(self) -> bool:
        """
        Indicates if this command should be the last one processed in a message.
        Useful for commands that change execution flow (e.g., focus changes).
        Default is False.
        """
        return False

    def get_additional_information(self) -> dict[Any, Any]:
        """
        Returns a dictionary with additional information about the command.
        Default is an empty dictionary.
        """
        return {}


class CommandRegistry:
    """Registry for all available commands."""

    def __init__(self):
        self._commands: dict[str, Command[Any]] = {}

    def register(self, command: Command[Any]) -> None:
        """Register a command instance."""
        if command.name in self._commands:
            # Handle potential duplicate registration (e.g., log warning)
            print(f"Warning: Command '{command.name}' is being re-registered.")
        self._commands[command.name] = command

    def get_command(self, name: str) -> Command[Any] | None:
        """Get a command instance by name."""
        return self._commands.get(name)

    def get_all_commands(self) -> dict[str, Command[Any]]:
        """Get all registered command instances."""
        # Return a copy to prevent external modification
        return self._commands.copy()

    def get_command_names(self) -> list[str]:
        """Get names of all registered commands."""
        return list(self._commands.keys())

    def clear(self) -> None:
        """Clear all registered commands (useful for testing)."""
        self._commands = {}
