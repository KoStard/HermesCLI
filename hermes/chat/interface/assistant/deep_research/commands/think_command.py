from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command


class ThinkCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "think",
            "A place for you to think before taking actions",
        )
        self.add_section("content", False, "Thinking content, as long as needed")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """This is a dummy command that doesn't trigger any actions"""
        # This command doesn't do anything, it's just a place for the assistant to think
        # No output needed for think command
