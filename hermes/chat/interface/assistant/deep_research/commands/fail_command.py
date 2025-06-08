import textwrap
from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research import ProblemStatus
from hermes.chat.interface.commands.command import Command as BaseCommand


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
        failure_message = args.get("message")
        self._validate_no_running_subtasks(context)
        self._attempt_fail_node(context, failure_message)

    def _validate_no_running_subtasks(self, context: ResearchCommandContextImpl) -> None:
        """Ensure no child nodes are still running before failing"""
        for child_node in context.current_node.list_child_nodes():
            if child_node.get_problem_status() == ProblemStatus.IN_PROGRESS:
                raise ValueError("Failed to mark the session as failed as there are running subtasks, cancel or wait for them.")

    def _attempt_fail_node(self, context: ResearchCommandContextImpl, failure_message: str | None) -> None:
        """Attempt to fail the node and handle any errors"""
        result = context.fail_node(message=failure_message)
        if not result:
            self._handle_fail_error(context, failure_message)

    def _handle_fail_error(self, context: ResearchCommandContextImpl, failure_message: str | None) -> None:
        """Handle errors when failing a node"""
        current_node_title = context.current_node.get_title()
        
        if self._is_root_node_with_message(context, failure_message):
            raise ValueError(f"Cannot pass a failure message from the root node '{current_node_title}' as there is no parent.")
        else:
            raise ValueError(f"Failed to mark problem as failed '{current_node_title}'.")

    def _is_root_node_with_message(self, context: ResearchCommandContextImpl, failure_message: str | None) -> bool:
        """Check if this is a root node trying to fail with a message"""
        return not context.current_node.get_parent() and failure_message
