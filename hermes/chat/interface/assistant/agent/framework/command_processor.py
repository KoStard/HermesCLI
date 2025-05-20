from typing import TYPE_CHECKING, Generic

from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory, CommandContextType
from hermes.chat.interface.assistant.agent.framework.engine_shutdown_requested_exception import EngineShutdownRequestedException
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.commands.command import (
    Command,
    CommandRegistry,
)
from hermes.chat.interface.commands.command_parser import CommandParser, ParseResult

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode
    from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor


class CommandProcessor(Generic[CommandContextType]):
    """Helper class to encapsulate command processing logic, operating within a TaskProcessor."""

    def __init__(
        self,
        task_processor: "TaskProcessor[CommandContextType]",
        command_parser: CommandParser,
        command_registry: CommandRegistry,
        command_context_factory: CommandContextFactory[CommandContextType],
    ):
        self.task_processor = task_processor
        self.command_parser = command_parser
        self.command_registry = command_registry
        self.command_context_factory = command_context_factory

    def process(self, text: str, current_task_tree_node: "TaskTreeNode"):
        """Process commands from text and return updated state."""
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            return self._handle_shutdown_command()

        self._add_message_to_history(text, current_task_tree_node)

        parsing_report, commands = self._parse_commands(text)

        failed_commands, needs_confirmation, status = self._execute_valid_commands(commands, current_task_tree_node, parsing_report)

        error_report = self._build_error_report(parsing_report, failed_commands)

        self._add_to_auto_reply(current_task_tree_node, error_report, needs_confirmation)

    def _handle_shutdown_command(self):
        """Handle shutdown command and return updated state."""
        raise EngineShutdownRequestedException()

    def _add_message_to_history(self, text: str, task_tree_node: "TaskTreeNode") -> None:
        """Add the assistant's message to history."""
        history = task_tree_node.get_research_node().get_history()
        history.add_message("assistant", text)

    def _parse_commands(self, text: str) -> tuple[str, list[ParseResult]]:
        """Parse commands from text and generate error report."""
        results = self.command_parser.parse_text(text)
        error_report = self.command_parser.generate_error_report(results)
        return error_report, results

    def _execute_valid_commands(
        self, commands: list[ParseResult], task_tree_node: "TaskTreeNode", parsing_error_report: str
    ) -> tuple[list[dict], bool, dict]:
        """Execute valid commands and return execution results."""
        has_parsing_errors = bool(parsing_error_report)
        status_map = {}
        failed_commands = []
        finish_or_fail_skipped = False
        last_command_reached = False

        for i, cmd in enumerate(commands):
            # Skip commands with syntax errors
            if cmd.errors or last_command_reached:
                continue

            cmd_key = f"{cmd.command_name}_{i}"
            line_num = cmd.errors[0].line_number if cmd.errors else None

            # Skip finish/fail commands if there are errors
            if self._is_terminal_command_with_errors(cmd, has_parsing_errors, failed_commands):
                finish_or_fail_skipped = True
                status_map[cmd_key] = self._create_skipped_status(cmd, "other errors detected in the message", line_num)
                continue

            # Execute the command
            result, exception = self._run_command(cmd, task_tree_node)

            # Handle execution result
            if exception:  # Error occurred
                failed_info = {"name": cmd.command_name, "status": f"failed: {str(exception)}", "line": line_num}
                status_map[cmd_key] = failed_info
                failed_commands.append(failed_info)
            elif result:  # Command executed successfully
                status_map[cmd_key] = {"name": cmd.command_name, "status": "success", "line": line_num}

                # Check if this command should be the last in the message
                if result.should_be_last_in_message():
                    last_command_reached = True

        return failed_commands, finish_or_fail_skipped, status_map

    def _is_terminal_command_with_errors(self, cmd: ParseResult, has_parsing_errors: bool, failed_commands: list[dict]) -> bool:
        """Check if this is a terminal command when there are errors."""
        is_terminal = cmd.command_name in ["finish_problem", "fail_problem"]
        has_errors = has_parsing_errors or bool(failed_commands)
        return is_terminal and has_errors

    def _create_skipped_status(self, cmd: ParseResult, reason: str, line: int | None) -> dict:
        """Create a status dict for skipped commands."""
        return {"name": cmd.command_name, "status": f"skipped: {reason}", "line": line}

    def _run_command(self, result: ParseResult, task_tree_node: "TaskTreeNode") -> tuple[Command | None, Exception | None]:
        """Execute a single command and return results."""
        command_name = result.command_name

        # Create command context
        context = self.command_context_factory.create_command_context(self.task_processor, task_tree_node, self)

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

        # Start with parsing errors
        final_report = parsing_report

        # Add execution errors if any exist
        if execution_errors:
            exec_report = ["### Execution Status Report:"]

            for error in execution_errors:
                cmd_name = error["name"]
                status = error["status"]
                line_info = f" at line {error['line']}" if error.get("line") is not None else ""
                exec_report.append(f"- Command '{cmd_name}'{line_info} {status}")

            exec_report_text = "\n".join(exec_report)

            # Combine reports appropriately
            if not final_report:
                final_report = exec_report_text
            elif "### Errors report:" in final_report:
                final_report += f"\n---\n{exec_report_text}"
            else:
                final_report += f"\n{exec_report_text}"

        # Ensure proper formatting
        if final_report and not ("### Errors report:" in final_report or "### Execution Status Report:" in final_report):
            final_report = f"### Errors report:\n{final_report}"

        return final_report

    def _add_to_auto_reply(self, task_tree_node: "TaskTreeNode", error_report: str, needs_confirmation: bool) -> None:
        """Add reports and confirmation requests to auto-reply."""
        auto_reply = task_tree_node.get_research_node().get_history().get_auto_reply_aggregator()

        # Add confirmation request if needed
        if needs_confirmation:
            auto_reply.add_confirmation_request(
                "You attempted to finish or fail the current problem, but there were errors "
                "in your message (see report below).\n"
                "Please review the errors. If you still want to finish/fail the problem, "
                "resend the `finish_problem` or `fail_problem` command **without** the errors.\n"
                "Otherwise, correct the errors and continue working on the problem."
            )

        # Add error report if any
        if error_report:
            auto_reply.add_error_report(error_report)

    def focus_down(self, subproblem_title: str, task_tree_node: "TaskTreeNode") -> bool:
        """Focus down to a subproblem."""
        research_node = task_tree_node.get_research_node()

        # Find target child node
        target_child = None
        for child in research_node.list_child_nodes():
            if child.get_title() == subproblem_title:
                target_child = child
                break

        if not target_child:
            return False

        # Update status and schedule subnode
        research_node.set_problem_status(ProblemStatus.PENDING)
        task_tree_node.add_and_schedule_subnode(target_child)
        return True

    def focus_up(self, message: str | None, task_tree_node: "TaskTreeNode") -> bool:
        """Mark task as finished and focus up to parent node."""
        research_node = task_tree_node.get_research_node()
        parent_node = research_node.get_parent()

        # Mark task as finished
        task_tree_node.finish()
        research_node.set_problem_status(ProblemStatus.FINISHED)

        # Handle root node case
        if not parent_node:
            research_node.set_resolution_message(message)
            return True

        # Add messages to parent's auto-reply
        self._add_status_message_to_parent(
            parent_node, research_node, "Task marked FINISHED, focusing back up.", message, "[Completion Message]: "
        )

        return True

    def fail_and_focus_up(self, message: str | None, task_tree_node: "TaskTreeNode") -> bool:
        """Mark task as failed and focus up to parent node."""
        research_node = task_tree_node.get_research_node()
        parent_node = research_node.get_parent()

        # Mark task as failed
        task_tree_node.finish()
        research_node.set_problem_status(ProblemStatus.FAILED)

        # Handle root node case
        if not parent_node:
            research_node.set_resolution_message(message)
            return True

        # Add messages to parent's auto-reply
        self._add_status_message_to_parent(
            parent_node, research_node, "Task marked FAILED, focusing back up.", message, "[Failure Message]: "
        )

        return True

    def _add_status_message_to_parent(
        self, parent_node: "ResearchNode", research_node: "ResearchNode", status_msg: str, custom_msg: str | None = None, prefix: str = ""
    ) -> None:
        """Add status and optional custom message to parent's auto-reply."""
        source_title = research_node.get_title()

        aggregator = parent_node.get_history().get_auto_reply_aggregator()

        # Add standard status message
        aggregator.add_internal_message_from(status_msg, source_title)

        # Add custom message if provided
        if custom_msg:
            aggregator.add_internal_message_from(f"{prefix}{custom_msg}", source_title)
