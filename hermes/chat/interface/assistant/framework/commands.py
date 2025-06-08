from abc import ABC, abstractmethod


class CommandContext(ABC):
    @abstractmethod
    def add_command_output(self, command_name: str, args: dict, output: str) -> None:
        """Add command output to be included in the automatic response for the current node."""
