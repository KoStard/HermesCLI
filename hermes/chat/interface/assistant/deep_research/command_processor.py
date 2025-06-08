from typing import TYPE_CHECKING, Any, Generic

from hermes.chat.interface.assistant.deep_research.commands import ResearchCommandContextFactory, ResearchCommandContextType
from hermes.chat.interface.assistant.deep_research.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.framework.engine_shutdown_requested_exception import EngineShutdownRequestedError
from hermes.chat.interface.commands.command import (
    Command,
    CommandRegistry,
)
from hermes.chat.interface.commands.command_parser import CommandParser, ParseResult

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode
    from hermes.chat.interface.assistant.deep_research.task_processor import TaskProcessor


class CommandProcessor(Generic[ResearchCommandContextType]):
    """Helper class to encapsulate command processing logic, operating within a TaskProcessor."""

    def __init__(
        self,
        task_processor: "TaskProcessor[ResearchCommandContextType]",
        command_parser: CommandParser,
        command_registry: CommandRegistry,
        command_context_factory: ResearchCommandContextFactory[ResearchCommandContextType],
    ):
        self.task_processor = task_processor
        self.command_parser = command_parser
        self.command_registry = command_registry
        self.command_context_factory = command_context_factory

    def process(self, text: str, current_node: "ResearchNode"):
        """Process commands from text and return updated state."""
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            return self._handle_shutdown_command()

        self._add_message_to_history(text, current_node)

        parsing_report, commands = self._parse_commands(text)

        failed_commands, needs_confirmation, status = self._execute_valid_commands(commands, current_node, parsing_report)

        error_report = self._build_error_report(parsing_report, failed_commands)

        self._add_to_auto_reply(current_node, error_report, needs_confirmation)
        return None

    def _handle_shutdown_command(self):
        """Handle shutdown command and return updated state."""
        raise EngineShutdownRequestedError()

    def _add_message_to_history(self, text: str, current_node: "ResearchNode") -> None:
        """Add the assistant's message to history."""
        history = current_node.get_history()
        history.add_message("assistant", text)

    def _parse_commands(self, text: str) -> tuple[str, list[ParseResult]]:
        """Parse commands from text and generate error report."""
        results = self.command_parser.parse_text(text)
        error_report = self.command_parser.generate_error_report(results)
        return error_report, results

    def _execute_valid_commands(
        self,
        commands: list[ParseResult],
        current_node: "ResearchNode",
        parsing_error_report: str,
    ) -> tuple[list[dict], bool, dict]:
        """Execute valid commands and return execution results."""
        has_parsing_errors = bool(parsing_error_report)
        status_map = {}
        failed_commands = []
        finish_or_fail_skipped = False

        for i, cmd in enumerate(commands):
            if cmd.errors:
                continue

            cmd_key = f"{cmd.command_name}_{i}"
            line_num = self._get_line_number(cmd)

            # Process the command
            finish_or_fail_skipped, status_map, failed_commands = self._process_command(
                cmd,
                has_parsing_errors,
                failed_commands,
                finish_or_fail_skipped,
                status_map,
                current_node,
                cmd_key,
                line_num,
            )

        return failed_commands, finish_or_fail_skipped, status_map

    def _get_line_number(self, cmd: ParseResult) -> int | None:
        """Extract line number from command result"""
        return cmd.errors[0].line_number if cmd.errors else None

    def _process_command(
        self,
        cmd: ParseResult,
        has_parsing_errors: bool,
        failed_commands: list[dict],
        finish_or_fail_skipped: bool,
        status_map: dict,
        current_node: "ResearchNode",
        cmd_key: str,
        line_num: int | None,
    ) -> tuple[bool, dict, list[dict]]:
        """Process a command and update tracking information"""
        # Skip terminal commands if there are errors
        if self._is_terminal_command_with_errors(cmd, has_parsing_errors, failed_commands):
            finish_or_fail_skipped = True
            status_map[cmd_key] = self._create_skipped_status(cmd, "other errors detected in the message", line_num)
            return finish_or_fail_skipped, status_map, failed_commands

        # Execute the command
        result, exception = self._run_command(cmd, current_node)

        # Update status based on execution result
        status_map, failed_commands = self._update_command_status(
            cmd,
            result,
            exception,
            status_map,
            failed_commands,
            cmd_key,
            line_num,
        )

        return finish_or_fail_skipped, status_map, failed_commands

    def _update_command_status(
        self,
        cmd: ParseResult,
        result: Any,
        exception: Exception | None,
        status_map: dict,
        failed_commands: list[dict],
        cmd_key: str,
        line_num: int | None,
    ) -> tuple[dict, list[dict]]:
        """Update status tracking based on command execution result"""
        if exception:  # Error occurred
            failed_info = {"name": cmd.command_name, "status": f"failed: {str(exception)}", "line": line_num}
            status_map[cmd_key] = failed_info
            failed_commands.append(failed_info)
        elif result:  # Command executed successfully
            status_map[cmd_key] = {"name": cmd.command_name, "status": "success", "line": line_num}
        return status_map, failed_commands

    def _is_terminal_command_with_errors(self, cmd: ParseResult, has_parsing_errors: bool, failed_commands: list[dict]) -> bool:
        """Check if this is a terminal command when there are errors."""
        is_terminal = cmd.command_name in ["finish_problem", "fail_problem"]
        has_errors = has_parsing_errors or bool(failed_commands)
        return is_terminal and has_errors

    def _create_skipped_status(self, cmd: ParseResult, reason: str, line: int | None) -> dict:
        """Create a status dict for skipped commands."""
        return {"name": cmd.command_name, "status": f"skipped: {reason}", "line": line}

    def _run_command(self, result: ParseResult, current_node: "ResearchNode") -> tuple[Command | None, Exception | None]:
        """Execute a single command and return results."""
        command_name = result.command_name

        # Create command context
        context = self.command_context_factory.create_command_context(self.task_processor, current_node, self)

        try:
            # Get and execute command
            assert command_name
            command = self.command_registry.get_command(command_name)
            if not command:
                raise ValueError(f"Command '{command_name}' not found in registry.")

            command.execute(context, result.args)
            return command, None

        except Exception as e:
            import traceback

            print(f"Error executing '{command_name}':")
            print(traceback.format_exc())
            return None, e

    def _build_error_report(self, parsing_report: str, execution_errors: list[dict]) -> str:
        """Build comprehensive error report from parsing and execution errors."""
        if not parsing_report and not execution_errors:
            return ""

        # Build report components
        parsing_section = self._format_parsing_errors(parsing_report)
        execution_section = self._format_execution_errors(execution_errors)

        # Combine reports
        return self._combine_error_reports(parsing_section, execution_section)

    def _format_parsing_errors(self, parsing_report: str) -> str:
        """Format parsing errors section"""
        if not parsing_report:
            return ""

        if "### Errors report:" not in parsing_report:
            return f"### Errors report:\n{parsing_report}"

        return parsing_report

    def _format_execution_errors(self, execution_errors: list[dict]) -> str:
        """Format execution errors into report section"""
        if not execution_errors:
            return ""

        lines = ["### Execution Status Report:"]

        for error in execution_errors:
            cmd_name = error["name"]
            status = error["status"]
            line_info = f" at line {error['line']}" if error.get("line") is not None else ""
            lines.append(f"- Command '{cmd_name}'{line_info} {status}")

        return "\n".join(lines)

    def _combine_error_reports(self, parsing_section: str, execution_section: str) -> str:
        """Combine parsing and execution error sections"""
        if not parsing_section:
            return execution_section

        if not execution_section:
            return parsing_section

        return f"{parsing_section}\n---\n{execution_section}"

    def _add_to_auto_reply(self, current_node: "ResearchNode", error_report: str, needs_confirmation: bool) -> None:
        """Add reports and confirmation requests to auto-reply."""
        auto_reply = current_node.get_history().get_auto_reply_aggregator()

        # Add confirmation request if needed
        if needs_confirmation:
            auto_reply.add_confirmation_request(
                "You attempted to finish or fail the current problem, but there were errors "
                "in your message (see report below).\n"
                "Please review the errors. If you still want to finish/fail the problem, "
                "resend the `finish_problem` or `fail_problem` command **without** the errors.\n"
                "Otherwise, correct the errors and continue working on the problem.",
            )

        # Add error report if any
        if error_report:
            auto_reply.add_error_report(error_report)

    def activate_subtask(self, subproblem_title: str, research_node: "ResearchNode") -> bool:
        """Focus down to a subproblem."""
        # Find target child node
        target_child = None
        for child in research_node.list_child_nodes():
            if child.get_title() == subproblem_title:
                target_child = child
                break

        if not target_child:
            return False

        if target_child.get_problem_status() == ProblemStatus.IN_PROGRESS:
            return True

        target_child.set_problem_status(ProblemStatus.READY_TO_START)
        return True

    def wait_for_subtask(self, subproblem_title: str, research_node: "ResearchNode"):
        # Find target child node
        target_child = None
        for child in research_node.list_child_nodes():
            if child.get_title() == subproblem_title:
                target_child = child
                break

        if not target_child:
            return

        research_node.add_child_node_to_wait(target_child)

    def finish_node(self, message: str | None, research_node: "ResearchNode") -> bool:
        """Mark task as finished and focus up to parent node."""
        parent_node = research_node.get_parent()

        research_node.set_problem_status(ProblemStatus.FINISHED)

        if not parent_node:
            # Handle root node case
            research_node.set_resolution_message(message)
        else:
            # Add messages to parent's auto-reply
            self._add_status_message_to_parent(
                parent_node,
                research_node,
                "Task marked FINISHED, focusing back up.",
                message,
                "[Completion Message]: ",
            )

        return True

    def fail_node(self, message: str | None, current_node: "ResearchNode") -> bool:
        """Mark task as failed and focus up to parent node."""
        research_node = current_node
        parent_node = research_node.get_parent()

        # Mark task as failed
        research_node.set_problem_status(ProblemStatus.FAILED)

        if not parent_node:
            # Handle root node case
            research_node.set_resolution_message(message)
        else:
            # Add messages to parent's auto-reply
            self._add_status_message_to_parent(
                parent_node,
                research_node,
                "Task marked FAILED, focusing back up.",
                message,
                "[Failure Message]: ",
            )

        return True

    def _add_status_message_to_parent(
        self,
        parent_node: "ResearchNode",
        research_node: "ResearchNode",
        status_msg: str,
        custom_msg: str | None = None,
        prefix: str = "",
    ) -> None:
        """Add status and optional custom message to parent's auto-reply."""
        source_title = research_node.get_title()

        aggregator = parent_node.get_history().get_auto_reply_aggregator()

        # Add standard status message
        aggregator.add_internal_message_from(status_msg, source_title)

        # Add custom message if provided
        if custom_msg:
            aggregator.add_internal_message_from(f"{prefix}{custom_msg}", source_title)
