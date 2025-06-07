from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command as BaseCommand


class MarkCriteriaAsDoneCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "mark_criteria_as_done",
            "Mark a criteria as completed",
        )
        self.add_section("criteria_number", True, "Number of the criteria to mark as done")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Mark criteria as done"""
        current_node = context.current_node

        # Get criteria list
        criteria_list = current_node.get_criteria()
        index = args["index"]

        # Check if index is valid
        if index < 0 or index >= len(criteria_list):
            context.add_command_output(self.name, args, f"Error: Criteria {args['criteria_number']} not found.")
            return

        # Update the criterion's completed status
        criteria_list[index].is_completed = True

        # Add confirmation output
        context.add_command_output(self.name, args, f"Criteria {args['criteria_number']} marked as done.")

    def transform_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert criteria_number to zero-based index"""
        if "criteria_number" in args:
            args["index"] = int(args["criteria_number"]) - 1  # Convert to 0-based index
        return args

    def validate(self, args: dict[str, Any]) -> list[str]:
        """Validate criteria number"""
        errors = super().validate(args)
        if "criteria_number" in args:
            try:
                index = int(args["criteria_number"]) - 1
                if index < 0:
                    errors.append(f"Criteria index must be positive, got: {index + 1}")
            except ValueError:
                errors.append(f"Invalid criteria index: '{args['criteria_number']}', must be a number")
        return errors
