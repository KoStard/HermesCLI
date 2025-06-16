import textwrap
from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research import ProblemStatus
from hermes.chat.interface.commands.command import Command


class FinishCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "finish_problem",
            help_text=textwrap.dedent("""\
            Finish the current problem. If there is a parent problem, it will become activated.
            You can optionally provide a message to the parent task using the ///message section.
            Ensure other commands are processed before sending this.
            Example with message:
            <<< finish_problem
            ///message
            Completed sub-analysis X, results attached in artifact Y.
            >>>
            Example without message:
            <<< finish_problem
            >>>

            If there are running subproblems, the finish command will fail. Either cancel the subproblems or wait for them.
            """),
        )
        # Add the optional message section
        self.add_section(
            "message",
            required=False,
            help_text="Optional message to pass to the parent task upon completion.",
        )

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        # Get the optional message from args
        completion_message = args.get("message")

        for child_node in context.current_node.list_child_nodes():
            if child_node.get_problem_status() == ProblemStatus.IN_PROGRESS:
                raise ValueError("Failed to finish the session as there are running subtasks.")

        # Pass the message to the context method
        result = context.finish_node(message=completion_message)

        if not result:
            raise ValueError("Failed to finish the session.")
