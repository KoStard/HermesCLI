from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from hermes.interface.assistant.deep_research_assistant.engine.command_context import (
    CommandContext,
)


class CommandSection:
    """Represents a section in a command (e.g., ///title, ///content)"""

    def __init__(self, name: str, required: bool = True, help_text: str = ""):
        self.name = name
        self.required = required
        self.help_text = help_text


class CommandType(Enum):
    """Types of commands supported by the system"""

    BLOCK = "block"  # Commands with sections like ///title, ///content
    SIMPLE = "simple"  # Commands without sections


class Command(ABC):
    """Base class for all commands"""

    def __init__(
        self,
        name: str,
        help_text: str = "",
        command_type: CommandType = CommandType.BLOCK,
    ):
        self.name = name
        self.help_text = help_text
        self.command_type = command_type
        self.sections: List[CommandSection] = []

    def add_section(
        self, name: str, required: bool = True, help_text: str = ""
    ) -> None:
        """Add a section to this command"""
        self.sections.append(CommandSection(name, required, help_text))

    def get_required_sections(self) -> List[str]:
        """Get names of all required sections"""
        return [section.name for section in self.sections if section.required]

    def get_all_sections(self) -> List[str]:
        """Get names of all sections"""
        return [section.name for section in self.sections]

    def get_section_help(self, section_name: str) -> str:
        """Get help text for a specific section"""
        for section in self.sections:
            if section.name == section_name:
                return section.help_text
        return ""

    @abstractmethod
    def execute(self, context: CommandContext, args: Dict[str, Any]) -> None:
        """Execute the command with the given arguments"""
        pass

    def add_output(
        self, context: CommandContext, args: Dict[str, Any], output: str
    ) -> None:
        """Add command output to be included in the automatic response"""
        context.add_command_output(self.name, args, output)

    def validate(self, args: Dict[str, Any]) -> List[str]:
        """Validate command arguments, return list of error messages"""
        errors = []
        for section in self.sections:
            if section.required and section.name not in args:
                errors.append(f"Missing required section '{section.name}'")
        return errors

    def transform_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Transform arguments before execution if needed"""
        return args

    def should_be_last_in_message(self):
        return False


class DefineCommand(Command):
    """Base class for commands that define or modify problems"""

    pass


class CommandRegistry:
    """Registry for all available commands"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CommandRegistry, cls).__new__(cls)
            cls._instance._commands = {}
        return cls._instance

    def register(self, command: Command) -> None:
        """Register a command"""
        self._commands[command.name] = command

    def get_command(self, name: str) -> Optional[Command]:
        """Get a command by name"""
        return self._commands.get(name)

    def get_problem_defined_interface_commands(self) -> Dict[str, Command]:
        """Get all registered commands"""
        return {
            name: command
            for name, command in self._commands.items()
            if not isinstance(command, DefineCommand)
        }

    def get_command_names(self) -> List[str]:
        """Get names of all registered commands"""
        return list(self._commands.keys())


# Helper function to register a command
def register_command(command: Command) -> Command:
    """Register a command and return it (decorator pattern)"""
    instance = command()
    CommandRegistry().register(instance)
    return command
