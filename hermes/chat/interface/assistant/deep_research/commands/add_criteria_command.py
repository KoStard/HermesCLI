from typing import Any

from hermes.chat.interface.assistant.deep_research.research.research_node_component.criteria_manager import Criterion
from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class AddCriteriaCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "add_criteria",
            "Add criteria for the current problem",
        )
        self.add_section("criteria", True, "Criteria text")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add criteria to the current problem"""
        current_node = context.current_node

        # Check if criteria already exists
        criteria_text = args["criteria"]
        existing_criteria = [c.content for c in current_node.get_criteria()]
        if criteria_text in existing_criteria:
            return

        # Create and add a new criterion
        criterion = Criterion(content=criteria_text)
        current_node.add_criterion(criterion)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Criteria '{criteria_text}' added.")
