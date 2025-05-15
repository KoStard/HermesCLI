
# Import the specific context for Deep Research
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research_assistant.engine.commands.command_context import (
    CommandContext,
)

# Import the registry creation function and type alias
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)

# Import other necessary components
from hermes.chat.interface.assistant.deep_research_assistant.engine.state_machine import StateMachineNode

# Import core command components from the new location
from hermes.chat.interface.commands.command import (
    Command,
    CommandRegistry,
)
from hermes.chat.interface.commands.command_parser import ParseResult

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.engine import DeepResearchEngine

class CommandProcessor:
    """Helper class to encapsulate command processing logic."""

    def __init__(self, engine: "DeepResearchEngine", command_registry: CommandRegistry):
        self.engine = engine
        self.command_parser = engine.command_parser # This parser was created with the same registry
        self.command_registry = command_registry

        # Results
        self.commands_executed = False
        self.final_error_report = ""
        self.execution_status = {}
        self._parsing_error_report = ""
        self._execution_failed_commands = []
        self._finish_or_fail_skipped = False

    def process(self, text: str, current_state_machine_node: "StateMachineNode") -> tuple[bool, str, dict]:
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

    def _handle_shutdown_request(self, text: str, current_state_machine_node: "StateMachineNode") -> bool:
        """Check for emergency shutdown code."""
        # Only shut down if the current node is the root node
        research_node = current_state_machine_node.get_research_node()
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower() \
        and research_node == self.engine.research.get_root_node():
            print("Shutdown requested for root node. Engine will await new instructions.")
            self.engine.finish_with_this_cycle()
            # Mark root as finished to signify completion of this phase
            research_node.set_problem_status(ProblemStatus.FINISHED)
            return True
        elif "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            print("Shutdown command ignored: Not currently focused on the root node.")
            # Optionally add an error message to auto-reply here
        return False

    def _add_assistant_message_to_history(self, text: str, current_state_machine_node: "StateMachineNode"):
        """Add the assistant's message to history for the current node."""
        history = current_state_machine_node.get_research_node().get_history()
        history.add_message("assistant", text)

    def _parse_and_validate_commands(self, text: str) -> list[ParseResult]:
        """Parse commands, handle syntax errors, and perform initial validation."""
        parse_results = self.command_parser.parse_text(text)

        # Generate report for any non-syntax parsing errors (e.g., missing sections)
        self._parsing_error_report = self.command_parser.generate_error_report(parse_results)

        return parse_results

    def _execute_commands(self, parse_results: list[ParseResult], current_state_machine_node: "StateMachineNode"):
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
            # else: command was None (e.g., unknown command, handled during parsing)

    def _execute_single_command(self, result: ParseResult, current_state_machine_node: "StateMachineNode") -> tuple[Command | None, Exception | None]:
        """Execute a single command and return the command object and any execution error."""
        command_name = result.command_name
        args = result.args
        error = None
        command: Command[CommandContext] | None = None  # Type hint for clarity
        command_context = CommandContext(self.engine, current_state_machine_node)

        try:
            # Use the provided command registry instance
            # Cast the retrieved command to the specific type expected
            command = self.command_registry.get_command(command_name)  # type: ignore

            if not command:
                # This should ideally be caught during parsing, but handle defensively
                raise ValueError(f"Command '{command_name}' not found in registry.")

            if not self.engine.is_root_problem_defined() and command_name != "define_problem":
                raise ValueError("Only 'define_problem' command is allowed before a problem is defined.")

            # Update command context before execution
            command_context.refresh_from_engine()

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

    def _update_auto_reply(self, current_state_machine_node: "StateMachineNode"):
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
