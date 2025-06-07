from typing import Any

from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class AddLogEntryCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "add_log_entry",
            "Add an entry to the permanent log",
        )
        self.add_section("content", True, "Content of the log entry")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add a log entry"""
        content = args.get("content", "")
        if content:
            context.add_to_permanent_log(content)
            # Add confirmation output
            context.add_command_output(self.name, args, "Log entry added.")
