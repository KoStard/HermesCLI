from typing import TYPE_CHECKING, Generic

from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory, CommandContextType
from hermes.chat.interface.assistant.agent.framework.research import ResearchNode # Added for type hint
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode
from hermes.chat.interface.commands.command import (
    Command,
    CommandRegistry,
)
from hermes.chat.interface.commands.command_parser import ParseResult

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.engine import AgentEngine

class CommandProcessor(Generic[CommandContextType]):
    """Helper class to encapsulate command processing logic."""

    def __init__(self, engine: "AgentEngine", command_registry: CommandRegistry, command_context_factory: CommandContextFactory[CommandContextType]):
        self.engine = engine
        self.command_parser = engine.command_parser # This parser was created with the same registry
        self.command_registry = command_registry
        self.command_context_factory = command_context_factory

        # Results
        self.commands_executed = False
        self.final_error_report = ""
        self.execution_status = {}
        self._parsing_error_report = ""
        self._execution_failed_commands = []
        self._finish_or_fail_skipped = False

    def process(self, text: str, current_state_machine_node: "TaskTreeNode") -> tuple[bool, str, dict]:
        """
        Process commands from text.

        Returns:
            tuple: (commands_executed, final_error_report, execution_status)
        """
        if self._handle_shutdown_request(text, current_state_machine_node):
            return (
                True,
                "System shutdown requested and executed.",
                {"shutdown": "success"},
            )

        self._add_assistant_message_to_history(text, current_state_machine_node)

        parse_results = self._parse_and_validate_commands(text)

        self._execute_commands(parse_results, current_state_machine_node)
        self._generate_final_report()
        self._update_auto_reply(current_state_machine_node)

        return self.commands_executed, self.final_error_report, self.execution_status

    def _handle_shutdown_request(self, text: str, current_state_machine_node: "TaskTreeNode") -> bool:
        """Check for emergency shutdown code."""
        # Only shut down if the current node is the root node
        research_node = current_state_machine_node.get_research_node()
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            self.engine.emergency_shutdown()
            return True
        return False

    def _add_assistant_message_to_history(self, text: str, current_state_machine_node: "TaskTreeNode"):
        """Add the assistant's message to history for the current node."""
        history = current_state_machine_node.get_research_node().get_history()
        history.add_message("assistant", text)

    def _parse_and_validate_commands(self, text: str) -> list[ParseResult]:
        """Parse commands, handle syntax errors, and perform initial validation."""
        parse_results = self.command_parser.parse_text(text)

        # Generate report for any non-syntax parsing errors (e.g., missing sections)
        self._parsing_error_report = self.command_parser.generate_error_report(parse_results)

        return parse_results

    def _execute_commands(self, parse_results: list[ParseResult], current_state_machine_node: "TaskTreeNode"):
        """Execute valid commands and track status."""
        command_that_should_be_last_reached = False
        has_parsing_errors = bool(self._parsing_error_report)  # Check if initial parsing found errors

        for i, result in enumerate(parse_results):
            # Skip execution if the command itself had parsing errors (e.g., missing required section)
            if result.errors:
                # Skipped commands that failed parsing or validation
                continue

            # Skip execution if a previous command required being last
            if command_that_should_be_last_reached:
                self._mark_as_skipped(
                    result,
                    i,
                    "came after a command that has to be the last in the message",
                )
                continue

            # Special handling for finish/fail commands
            is_finish_or_fail = result.command_name in [
                "finish_problem",
                "fail_problem",
            ]
            has_any_errors_so_far = has_parsing_errors or bool(self._execution_failed_commands)

            if is_finish_or_fail and has_any_errors_so_far:
                self._finish_or_fail_skipped = True
                self._mark_as_skipped(
                    result,
                    i,
                    "other errors detected in the message, do you really want to go ahead?",
                )
                continue

            # --- Execute the command ---
            command, execution_error = self._execute_single_command(result, current_state_machine_node)

            # --- Update Status ---
            cmd_key = f"{result.command_name}_{i}"
            line_num = result.errors[0].line_number if result.errors else None  # Should be None here

            if execution_error:
                failed_info = {
                    "name": result.command_name,
                    "status": f"failed: {str(execution_error)}",
                    "line": line_num,
                }
                self.execution_status[cmd_key] = failed_info
                self._execution_failed_commands.append(failed_info)
            elif command:  # Command executed successfully
                self.execution_status[cmd_key] = {
                    "name": result.command_name,
                    "status": "success",
                    "line": line_num,
                }
                self.commands_executed = True
                if command.should_be_last_in_message():
                    command_that_should_be_last_reached = True

    def _execute_single_command(self, result: ParseResult, current_state_machine_node: "TaskTreeNode") -> tuple[Command | None, Exception | None]:
        """Execute a single command and return the command object and any execution error."""
        command_name = result.command_name
        args = result.args
        error = None
        command: Command[CommandContextType] | None = None  # Type hint for clarity
        command_context = self.command_context_factory.create_command_context(
            self.engine, current_state_machine_node, self
        )

        try:
            # Use the provided command registry instance
            # Cast the retrieved command to the specific type expected
            command = self.command_registry.get_command(command_name)  # type: ignore

            if not command:
                # This should ideally be caught during parsing, but handle defensively
                raise ValueError(f"Command '{command_name}' not found in registry.")

            if not self.engine.is_research_initiated() and command_name != "define_problem":
                raise ValueError("Only 'define_problem' command is allowed before a problem is defined.")

            # Execute the command
            command.execute(command_context, args)

        except ValueError as e:
            error = e
        except Exception as e:
            # Catch unexpected errors during execution
            error = e
            import traceback

            print(f"Unexpected error executing command '{command_name}':")
            print(traceback.format_exc())

        return command, error

    def _mark_as_skipped(self, result: ParseResult, index: int, reason: str):
        """Update execution status for a skipped command."""
        cmd_key = f"{result.command_name}_{index}"
        line_num = result.errors[0].line_number if result.errors else None
        self.execution_status[cmd_key] = {
            "name": result.command_name,
            "status": f"skipped: {reason}",
            "line": line_num,
        }

    def _generate_final_report(self):
        """Combine parsing and execution errors into the final report."""
        self.final_error_report = self._parsing_error_report

        execution_report = "\n### Execution Status Report:\n"
        for info in self._execution_failed_commands:
            cmd_name = info["name"]
            status = info["status"]
            line_num = info["line"]
            line_info = f" at line {line_num}" if line_num is not None else ""
            execution_report += f"- Command '{cmd_name}'{line_info} {status}\n"

        if not self.final_error_report:
            self.final_error_report = execution_report.strip()
        else:
            # Add separator if there were also parsing errors
            if self._parsing_error_report and "### Errors report:" in self._parsing_error_report:
                self.final_error_report += "\n---\n" + execution_report
            else:  # Only execution errors or syntax errors
                self.final_error_report += "\n" + execution_report

    def _update_auto_reply(self, current_state_machine_node: "TaskTreeNode"):
        """Add error reports and confirmation requests to the auto-reply aggregator."""
        auto_reply_generator = current_state_machine_node.get_research_node().get_history().get_auto_reply_aggregator()

        # Add confirmation request if finish/fail was skipped
        if self._finish_or_fail_skipped:
            confirmation_msg = (
                "You attempted to finish or fail the current problem, but there were errors "
                "in your message (see report below).\n"
                "Please review the errors. If you still want to finish/fail the problem, "
                "resend the `finish_problem` or `fail_problem` command **without** the errors.\n"
                "Otherwise, correct the errors and continue working on the problem."
            )
            auto_reply_generator.add_confirmation_request(confirmation_msg)

        # Add the combined error report
        if self.final_error_report:
            # Ensure the report starts with the expected header if only execution errors are present
            if "### Errors report:" not in self.final_error_report and "### Execution Status Report:" not in self.final_error_report:
                report_to_add = "### Errors report:\n" + self.final_error_report
            else:
                report_to_add = self.final_error_report
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

    def focus_up(self, message: str | None, current_state_machine_node: "TaskTreeNode") -> bool:
        """
        Schedule focus up to the parent problem after the current cycle is complete.
        Adds a standard notification and an optional custom message from the child
        to the parent's auto-reply.

        Args:
            message: Optional custom message from the child node to the parent.
            current_state_machine_node: The current state machine node.

        Returns:
            bool: True if successful, False otherwise (e.g., no current node).
        """
        current_research_node = current_state_machine_node.get_research_node()
        parent_node = current_research_node.get_parent()
        current_state_machine_node.finish()

        # If this is the root node (no parent), we're done
        if parent_node is None:
            # Mark the root node as FINISHED
            current_research_node.set_problem_status(ProblemStatus.FINISHED)
            # Store the completion message if provided
            # Root node finished. Set awaiting flag.
            if message:
                self.engine.root_completion_message = message  # Store final message if any
            # Current node will finish at the end of this cycle
            print(f"Root node '{current_research_node.get_title()}' finished. Engine awaiting new instruction.")
            return True

        # Mark the current non-root node as FINISHED
        current_research_node.set_problem_status(ProblemStatus.FINISHED)

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

    def fail_and_focus_up(self, message: str | None, current_state_machine_node: "TaskTreeNode") -> bool:
        """
        Mark the current problem as FAILED, schedule focus up, and add notifications
        (standard and optional custom) to the parent's auto-reply.

        Args:
            message: Optional custom message explaining the failure.
            current_state_machine_node: The current state machine node.

        Returns:
            bool: True if successful, False otherwise (e.g., no current node).
        """
        current_research_node = current_state_machine_node.get_research_node()
        parent_node = current_research_node.get_parent()
        current_state_machine_node.finish()

        # If this is the root node (no parent), we're done
        if parent_node is None:
            # Mark the root node as FAILED
            current_research_node.set_problem_status(ProblemStatus.FAILED)
            # Store the failure message if provided
            # Root node failed. Set awaiting flag.
            if message:
                self.engine.root_completion_message = message  # Store final message if any
            print(f"Root node '{current_research_node.get_title()}' failed. Engine awaiting new instruction.")
            return True

        # Mark the current non-root node as FAILED
        current_research_node.set_problem_status(ProblemStatus.FAILED)

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
