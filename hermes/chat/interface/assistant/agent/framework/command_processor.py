from typing import TYPE_CHECKING, Generic

from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory, CommandContextType
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.task_processing_state import TaskProcessingState
from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode
from hermes.chat.interface.commands.command import (
    Command,
    CommandRegistry,
)
from hermes.chat.interface.commands.command_parser import CommandParser, ParseResult

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor


class CommandProcessor(Generic[CommandContextType]):
    """Helper class to encapsulate command processing logic, operating within a TaskProcessor."""

    def __init__(
        self,
        task_processor: "TaskProcessor[CommandContextType]",
        command_parser: CommandParser,
        command_registry: CommandRegistry,
        command_context_factory: CommandContextFactory[CommandContextType]
    ):
        self.task_processor = task_processor
        self.command_parser = command_parser
        self.command_registry = command_registry
        self.command_context_factory = command_context_factory

    def process(self, text: str, current_task_tree_node: "TaskTreeNode", initial_state: TaskProcessingState) -> TaskProcessingState:
        """
        Process commands from text. Operates on and returns a TaskProcessingState.
        """
        current_processing_state = initial_state

        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            return current_processing_state.with_engine_shutdown_requested(True).with_command_results(
                executed=True,
                report="System shutdown requested.", # Message adjusted
                status={"shutdown_request": "processed"}, # Status adjusted
            )

        self._add_assistant_message_to_history(text, current_task_tree_node)

        parsing_error_report, parse_results = self._parse_and_validate_commands(text)

        (
            commands_executed,
            execution_failed_commands,
            finish_or_fail_skipped,
            execution_status,
        ) = self._execute_commands(parse_results, current_task_tree_node, parsing_error_report)

        final_error_report = self._generate_final_report(parsing_error_report, execution_failed_commands)
        self._update_auto_reply(current_task_tree_node, final_error_report, finish_or_fail_skipped)

        # Check if current task is now finished/failed due to command execution
        current_node_status = current_task_tree_node.get_research_node().get_problem_status()
        task_is_terminal = current_node_status in [ProblemStatus.FINISHED, ProblemStatus.FAILED]

        # Update the state based on command execution outcomes
        # engine_shutdown_requested is handled if "SHUT_DOWN" was in text
        # current_task_finished_or_failed is set if node status became terminal
        updated_state = current_processing_state.with_command_results(
            executed=commands_executed,
            report=final_error_report,
            status=execution_status
        ).with_current_task_finished_or_failed(
            current_processing_state.current_task_finished_or_failed or task_is_terminal
        )
        return updated_state


    def _add_assistant_message_to_history(self, text: str, current_task_tree_node: "TaskTreeNode"):
        """Add the assistant's message to history for the current node."""
        history = current_task_tree_node.get_research_node().get_history()
        history.add_message("assistant", text)

    def _parse_and_validate_commands(self, text: str) -> tuple[str, list[ParseResult]]:
        """Parse commands, handle syntax errors, and perform initial validation."""
        parse_results = self.command_parser.parse_text(text)
        parsing_error_report = self.command_parser.generate_error_report(parse_results)
        return parsing_error_report, parse_results

    def _execute_commands(
        self, parse_results: list[ParseResult], current_task_tree_node: "TaskTreeNode", parsing_error_report: str
    ) -> tuple[bool, list[dict], bool, dict]:
        """Execute valid commands and track status.
        Returns:
            commands_executed (bool)
            execution_failed_commands (list[dict])
            finish_or_fail_skipped (bool)
            execution_status (dict)
        """
        commands_executed = False
        execution_failed_commands: list[dict] = []
        finish_or_fail_skipped = False
        execution_status: dict = {}

        command_that_should_be_last_reached = False
        has_parsing_errors = bool(parsing_error_report)

        for i, result in enumerate(parse_results):
            cmd_key = f"{result.command_name}_{i}"
            line_num = result.errors[0].line_number if result.errors else None

            if result.errors: # Skipped due to parsing errors in this command
                continue

            if command_that_should_be_last_reached:
                execution_status[cmd_key] = self._mark_as_skipped_dict(result, "came after a command that has to be the last in the message", line_num)
                continue

            is_finish_or_fail = result.command_name in ["finish_problem", "fail_problem"]
            has_any_errors_so_far = has_parsing_errors or bool(execution_failed_commands)

            if is_finish_or_fail and has_any_errors_so_far:
                finish_or_fail_skipped = True
                execution_status[cmd_key] = self._mark_as_skipped_dict(result, "other errors detected in the message, do you really want to go ahead?", line_num)
                continue

            command, execution_error = self._execute_single_command(result, current_task_tree_node)

            if execution_error:
                failed_info = {
                    "name": result.command_name, "status": f"failed: {str(execution_error)}", "line": line_num
                }
                execution_status[cmd_key] = failed_info
                execution_failed_commands.append(failed_info)
            elif command:
                execution_status[cmd_key] = {"name": result.command_name, "status": "success", "line": line_num}
                commands_executed = True
                if command.should_be_last_in_message():
                    command_that_should_be_last_reached = True

        return commands_executed, execution_failed_commands, finish_or_fail_skipped, execution_status


    def _execute_single_command(
        self, result: ParseResult, current_task_tree_node: "TaskTreeNode"
    ) -> tuple[Command | None, Exception | None]:
        """
        Execute a single command.
        Returns:
            command (Command | None): The executed command object if successful.
            error (Exception | None): Exception if execution failed.
        """
        command_name = result.command_name
        args = result.args
        error = None
        command: Command[CommandContextType] | None = None

        command_context = self.command_context_factory.create_command_context(
            self.task_processor, current_task_tree_node, self
        )

        try:
            command = self.command_registry.get_command(command_name) # type: ignore
            if not command:
                raise ValueError(f"Command '{command_name}' not found in registry.")

            command.execute(command_context, args)

        except ValueError as e:
            error = e
        except Exception as e:
            error = e
            import traceback
            print(f"Unexpected error executing command '{command_name}':")
            print(traceback.format_exc())

        return command, error

    def _mark_as_skipped_dict(self, result: ParseResult, reason: str, line_num: int | None) -> dict:
        """Helper to create a skipped status dictionary."""
        return {
            "name": result.command_name,
            "status": f"skipped: {reason}",
            "line": line_num,
        }

    def _generate_final_report(self, parsing_error_report: str, execution_failed_commands: list[dict]) -> str:
        """Combine parsing and execution errors into the final report."""
        final_error_report = parsing_error_report

        execution_report_parts = []
        if execution_failed_commands:
            execution_report_parts.append("\n### Execution Status Report:")
            for info in execution_failed_commands:
                cmd_name = info["name"]
                status = info["status"]
                line_num = info["line"]
                line_info = f" at line {line_num}" if line_num is not None else ""
                execution_report_parts.append(f"- Command '{cmd_name}'{line_info} {status}")

        full_execution_report = "\n".join(execution_report_parts)

        if not final_error_report:
            final_error_report = full_execution_report.strip()
        elif execution_failed_commands : # Only add if there are execution errors
            if parsing_error_report and "### Errors report:" in parsing_error_report:
                final_error_report += "\n---\n" + full_execution_report
            else:
                final_error_report += "\n" + full_execution_report
        return final_error_report

    def _update_auto_reply(self, current_state_machine_node: "TaskTreeNode", final_error_report: str, finish_or_fail_skipped: bool):
        """Add error reports and confirmation requests to the auto-reply aggregator."""
        auto_reply_generator = current_state_machine_node.get_research_node().get_history().get_auto_reply_aggregator()

        if finish_or_fail_skipped:
            confirmation_msg = (
                "You attempted to finish or fail the current problem, but there were errors "
                "in your message (see report below).\n"
                "Please review the errors. If you still want to finish/fail the problem, "
                "resend the `finish_problem` or `fail_problem` command **without** the errors.\n"
                "Otherwise, correct the errors and continue working on the problem."
            )
            auto_reply_generator.add_confirmation_request(confirmation_msg)

        if final_error_report:
            report_to_add = final_error_report
            if "### Errors report:" not in report_to_add and "### Execution Status Report:" not in report_to_add:
                report_to_add = "### Errors report:\n" + report_to_add
            auto_reply_generator.add_error_report(report_to_add)


    def focus_down(self, subproblem_title: str, current_state_machine_node: "TaskTreeNode") -> bool:
        """
        Schedule focus down to a subproblem after the current cycle is complete.

        Args:
            subproblem_title: Title of the subproblem to focus on.
            current_state_machine_node: The current state machine node.

        Returns:
            bool: True if successful, False otherwise.
        """
        current_research_node = current_state_machine_node.get_research_node()

        # Find the child node with matching title
        child_nodes = current_research_node.list_child_nodes()
        target_child = None
        for child in child_nodes:
            if child.get_title() == subproblem_title:
                target_child = child
                break

        if target_child is None:
            return False

        # Set the parent to PENDING
        current_research_node.set_problem_status(ProblemStatus.PENDING)

        # Add the child node to the state machine
        current_state_machine_node.add_and_schedule_subnode(target_child)

        return True

    def focus_up(
        self, message: str | None, current_state_machine_node: "TaskTreeNode"
    ) -> bool:
        """
        Schedule focus up to the parent problem.
        Args:
            message: Optional custom message from the child node to the parent.
            current_state_machine_node: The current state machine node.
        Returns:
            Tuple of (success: bool, should_finish_engine: bool, root_completion_message: str | None)
        """
        current_research_node = current_state_machine_node.get_research_node()
        parent_node = current_research_node.get_parent()
        current_state_machine_node.finish() # Mark task tree node as finished

        if parent_node is None: # Current node is the root node
            current_research_node.set_problem_status(ProblemStatus.FINISHED)
            print(f"Root node '{current_research_node.get_title()}' finished. Engine awaiting new instruction.")
            return True

        current_research_node.set_problem_status(ProblemStatus.FINISHED) # Non-root node

        # --- Add messages to parent's auto-reply BEFORE scheduling focus ---
        parent_history = parent_node.get_history()
        parent_auto_reply_aggregator = parent_history.get_auto_reply_aggregator()

        # 1. Always add the standard status message
        parent_auto_reply_aggregator.add_internal_message_from(
            "Task marked FINISHED, focusing back up.", current_research_node.get_title()
        )

        # 2. If a custom message was provided, add it as well
        if message:
            # Prefix the custom message for clarity
            parent_auto_reply_aggregator.add_internal_message_from(
                f"[Completion Message]: {message}", current_research_node.get_title()
            )

        # The node will be finished at the end of this cycle
        # State machine will automatically return to parent node via next()
        return True

    def fail_and_focus_up(
        self, message: str | None, current_state_machine_node: "TaskTreeNode"
    ) -> bool:
        """
        Mark the current problem as FAILED and schedule focus up.
        Args:
            message: Optional custom message explaining the failure.
            current_state_machine_node: The current state machine node.
        Returns:
            Tuple of (success: bool, should_finish_engine: bool, root_completion_message: str | None)
        """
        current_research_node = current_state_machine_node.get_research_node()
        parent_node = current_research_node.get_parent()
        current_state_machine_node.finish() # Mark task tree node as finished


        if parent_node is None: # Current node is the root node
            current_research_node.set_problem_status(ProblemStatus.FAILED)
            print(f"Root node '{current_research_node.get_title()}' failed. Engine awaiting new instruction.")
            return True

        current_research_node.set_problem_status(ProblemStatus.FAILED) # Non-root node

        # --- Add messages to parent's auto-reply BEFORE scheduling focus ---
        parent_history = parent_node.get_history()
        parent_auto_reply_aggregator = parent_history.get_auto_reply_aggregator()

        # 1. Always add the standard status message
        parent_auto_reply_aggregator.add_internal_message_from(
            "Task marked FAILED, focusing back up.", current_research_node.get_title()
        )

        # 2. If a custom failure message was provided, add it as well
        if message:
            # Prefix the custom message for clarity
            parent_auto_reply_aggregator.add_internal_message_from(
                f"[Failure Message]: {message}", current_research_node.get_title()
            )

        # The node will be finished at the end of this cycle
        # State machine will automatically return to parent node via next()
        return True
