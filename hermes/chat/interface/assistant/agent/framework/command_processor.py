from typing import TYPE_CHECKING, Generic

from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory, CommandContextType
from hermes.chat.interface.assistant.agent.framework.engine_processing_state import EngineProcessingState
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
        self.engine = engine  # Engine reference is still needed for context and some direct calls
        self.command_parser = engine.command_parser # This parser was created with the same registry
        self.command_registry = command_registry
        self.command_context_factory = command_context_factory

    def process(self, text: str, current_state_machine_node: "TaskTreeNode", initial_engine_state: EngineProcessingState) -> EngineProcessingState:
        """
        Process commands from text. Operates on and returns an EngineProcessingState.
        """
        current_processing_state = initial_engine_state

        if self._handle_shutdown_request(text, current_state_machine_node):
            # If shutdown is requested, engine's emergency_shutdown is called,
            # and we return a state indicating it should finish.
            return current_processing_state.with_should_finish(True).with_command_results(
                executed=True,
                report="System shutdown requested and executed.",
                status={"shutdown": "success"},
            )

        self._add_assistant_message_to_history(text, current_state_machine_node)

        parsing_error_report, parse_results = self._parse_and_validate_commands(text)

        (
            commands_executed,
            execution_failed_commands,
            finish_or_fail_skipped,
            execution_status,
            accumulated_should_finish, # From focus_up/fail_and_focus_up commands
            accumulated_root_message   # From focus_up/fail_and_focus_up commands
        ) = self._execute_commands(parse_results, current_state_machine_node, parsing_error_report)

        final_error_report = self._generate_final_report(parsing_error_report, execution_failed_commands)
        self._update_auto_reply(current_state_machine_node, final_error_report, finish_or_fail_skipped)

        new_should_finish = current_processing_state.should_finish or accumulated_should_finish
        new_root_message = accumulated_root_message if accumulated_root_message is not None else current_processing_state.root_completion_message

        return current_processing_state.with_command_results(
            executed=commands_executed,
            report=final_error_report,
            status=execution_status
        ).with_should_finish(new_should_finish).with_root_completion_message(new_root_message)


    def _handle_shutdown_request(self, text: str, current_state_machine_node: "TaskTreeNode") -> bool:
        """Check for emergency shutdown code. Calls engine's shutdown if detected."""
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            self.engine.emergency_shutdown() # emergency_shutdown sets a flag on the engine itself
            return True
        return False

    def _add_assistant_message_to_history(self, text: str, current_state_machine_node: "TaskTreeNode"):
        """Add the assistant's message to history for the current node."""
        history = current_state_machine_node.get_research_node().get_history()
        history.add_message("assistant", text)

    def _parse_and_validate_commands(self, text: str) -> tuple[str, list[ParseResult]]:
        """Parse commands, handle syntax errors, and perform initial validation."""
        parse_results = self.command_parser.parse_text(text)
        parsing_error_report = self.command_parser.generate_error_report(parse_results)
        return parsing_error_report, parse_results

    def _execute_commands(
        self, parse_results: list[ParseResult], current_state_machine_node: "TaskTreeNode", parsing_error_report: str
    ) -> tuple[bool, list[dict], bool, dict, bool, str | None]:
        """Execute valid commands and track status.
        Returns:
            commands_executed (bool)
            execution_failed_commands (list[dict])
            finish_or_fail_skipped (bool)
            execution_status (dict)
            accumulated_should_finish (bool) - True if any focus_up/fail_and_focus_up on root occurs
            accumulated_root_message (str | None) - Message from focus_up/fail_and_focus_up on root
        """
        commands_executed = False
        execution_failed_commands: list[dict] = []
        finish_or_fail_skipped = False
        execution_status: dict = {}

        command_that_should_be_last_reached = False
        has_parsing_errors = bool(parsing_error_report)

        # For effects from focus_up/fail_and_focus_up commands
        accumulated_should_finish = False
        accumulated_root_message: str | None = None


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

            command, execution_error, cmd_should_finish, cmd_root_message = self._execute_single_command(result, current_state_machine_node)

            if cmd_should_finish: # prioritize this signal
                accumulated_should_finish = True
            if cmd_root_message is not None: # prioritize this signal
                accumulated_root_message = cmd_root_message


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

        return commands_executed, execution_failed_commands, finish_or_fail_skipped, execution_status, accumulated_should_finish, accumulated_root_message

    def _execute_single_command(
        self, result: ParseResult, current_state_machine_node: "TaskTreeNode"
    ) -> tuple[Command | None, Exception | None, bool | None, str | None]:
        """
        Execute a single command.
        Returns:
            command (Command | None): The executed command object if successful.
            error (Exception | None): Exception if execution failed.
            should_finish_engine (bool): True if this command implies the engine should finish (e.g. focus_up on root).
            root_completion_message (str | None): Message if this command implies a root completion message.
        """
        command_name = result.command_name
        args = result.args
        error = None
        command: Command[CommandContextType] | None = None

        # Signals from commands that change focus (focus_up, fail_and_focus_up)
        cmd_should_finish_engine = False
        cmd_root_completion_message: str | None = None

        command_context = self.command_context_factory.create_command_context(
            self.engine, current_state_machine_node, self
        )

        try:
            command = self.command_registry.get_command(command_name) # type: ignore
            if not command:
                raise ValueError(f"Command '{command_name}' not found in registry.")
            if not self.engine.is_research_initiated() and command_name != "define_problem":
                raise ValueError("Only 'define_problem' command is allowed before a problem is defined.")

            command.execute(command_context, args) # This might call focus_up/fail_and_focus_up via context

            # Retrieve any focus-related signals that were set on the context
            # by focus_up/fail_and_focus_up calls during command.execute().
            # The CommandContext (base class) now defines these methods, and
            # CommandContextImpl (concrete class) implements them by storing
            # results from processor.focus_up/fail_and_focus_up.
            # These "pop" methods retrieve the value and clear it internally.
            cmd_should_finish_engine = command_context.pop_engine_finish_signal()
            cmd_root_completion_message = command_context.pop_root_completion_message_signal()

        except ValueError as e:
            error = e
        except Exception as e:
            error = e
            import traceback
            print(f"Unexpected error executing command '{command_name}':")
            print(traceback.format_exc())

        return command, error, cmd_should_finish_engine, cmd_root_completion_message

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
    ) -> tuple[bool, bool, str | None]:
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

        should_finish_engine = False
        root_completion_message_update: str | None = None

        if parent_node is None: # Current node is the root node
            current_research_node.set_problem_status(ProblemStatus.FINISHED)
            should_finish_engine = True # Engine loop should stop or wait for new instruction
            if message:
                root_completion_message_update = message
            # self.engine.root_completion_message is now handled by EngineProcessingState
            print(f"Root node '{current_research_node.get_title()}' finished. Engine awaiting new instruction.")
            return True, should_finish_engine, root_completion_message_update

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
        return True, should_finish_engine, root_completion_message_update

    def fail_and_focus_up(
        self, message: str | None, current_state_machine_node: "TaskTreeNode"
    ) -> tuple[bool, bool, str | None]:
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

        should_finish_engine = False
        root_completion_message_update: str | None = None

        if parent_node is None: # Current node is the root node
            current_research_node.set_problem_status(ProblemStatus.FAILED)
            should_finish_engine = True # Engine loop should stop or wait for new instruction
            if message:
                root_completion_message_update = message
            # self.engine.root_completion_message is now handled by EngineProcessingState
            print(f"Root node '{current_research_node.get_title()}' failed. Engine awaiting new instruction.")
            return True, should_finish_engine, root_completion_message_update

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
        return True, should_finish_engine, root_completion_message_update
