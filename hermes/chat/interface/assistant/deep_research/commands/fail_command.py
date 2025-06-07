import textwrap
from typing import Any

from hermes.chat.interface.assistant.deep_research.research import ProblemStatus
from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class FailCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "fail_problem",
            help_text=textwrap.dedent("""\
            Mark the current problem as FAILED. If there is a parent problem, it will become activated.
            You can optionally provide a message to the parent task using the ///message section explaining the failure.
            Ensure other commands are processed before sending this.
            Example with message:
            <<< fail_problem
            ///message
            Could not proceed due to missing external data source X.
            >>>
            Example without message:
            <<< fail_problem
            >>>

            If there are running subproblems, the fail command will be rejected. Either cancel the subproblems or wait for them.
            """),
        )
        # Add the optional message section
        self.add_section(
            "message",
            required=False,
            help_text="Optional message to pass to the parent task explaining the failure.",
        )

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        # Get the optional message from args
        failure_message = args.get("message")

        for child_node in context.current_node.list_child_nodes():
            if child_node.get_problem_status() == ProblemStatus.IN_PROGRESS:
                raise ValueError("Failed to mark the session as failed as there are running subtasks, cancel or wait for them.")

        # Pass the message to the context method
        result = context.fail_node(message=failure_message)

        if not result:
            # Keep existing error handling, refine slightly for root node case
            current_node_title = context.current_node.get_title()

            if not context.current_node.get_parent():
                # Specific error if it's the root node trying to fail with a message meant for a parent
                if failure_message:
                    raise ValueError(f"Cannot pass a failure message from the root node '{current_node_title}' as there is no parent.")
            else:
                # General failure case if not root or root without message
                raise ValueError(f"Failed to mark problem as failed '{current_node_title}'.")
