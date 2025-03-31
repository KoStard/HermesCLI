from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .command import Command, CommandRegistry
from .command_parser import CommandParser, ParseResult
from .command_context import CommandContext

# Import commands to ensure they're registered
from .file_system import FileSystem, Node, ProblemStatus
from .history import ChatHistory, AutoReply, ChatMessage
from .interface import DeepResearcherInterface
from .llm_interface import LLMInterface
from .logger import DeepResearchLogger
from .status_printer import StatusPrinter
from .report_generator import ReportGenerator


class _CommandProcessor:
    """Helper class to encapsulate command processing logic."""

    def __init__(self, engine: "DeepResearchEngine"):
        self.engine = engine
        self.command_parser = engine.command_parser
        self.chat_history = engine.chat_history
        self.current_node = engine.current_node
        self.command_context = engine.command_context

        # Results
        self.commands_executed = False
        self.final_error_report = ""
        self.execution_status = {}
        self._parsing_error_report = ""
        self._execution_failed_commands = []
        self._finish_or_fail_skipped = False

    def process(self, text: str) -> Tuple[bool, str, Dict]:
        """
        Process commands from text.

        Returns:
            tuple: (commands_executed, final_error_report, execution_status)
        """
        if self._handle_shutdown_request(text):
            return (
                True,
                "System shutdown requested and executed.",
                {"shutdown": "success"},
            )

        self._add_assistant_message_to_history(text)

        parse_results = self._parse_and_validate_commands(text)

        self._execute_commands(parse_results)
        self._generate_final_report()
        self._update_auto_reply()

        return self.commands_executed, self.final_error_report, self.execution_status

    def _handle_shutdown_request(self, text: str) -> bool:
        """Check for emergency shutdown code."""
        if "SHUT_DOWN_DEEP_RESEARCHER".lower() in text.lower():
            self.engine.finished = True
            return True
        return False

    @property
    def _current_history_tag(self):
        if self.current_node:
            return self.current_node.title
        else:
            return "no_node"

    def _add_assistant_message_to_history(self, text: str):
        """Add the assistant's message to history for the current node."""
        self.chat_history.add_message("assistant", text, self._current_history_tag)

    def _parse_and_validate_commands(self, text: str) -> List[ParseResult]:
        """Parse commands, handle syntax errors, and perform initial validation."""
        parse_results = self.command_parser.parse_text(text)

        # Generate report for any non-syntax parsing errors (e.g., missing sections)
        self._parsing_error_report = self.command_parser.generate_error_report(
            parse_results
        )

        return parse_results

    def _execute_commands(self, parse_results: List[ParseResult]):
        """Execute valid commands and track status."""
        command_that_should_be_last_reached = False
        has_parsing_errors = bool(
            self._parsing_error_report
        )  # Check if initial parsing found errors

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
            has_any_errors_so_far = has_parsing_errors or bool(
                self._execution_failed_commands
            )

            if is_finish_or_fail and has_any_errors_so_far:
                self._finish_or_fail_skipped = True
                self._mark_as_skipped(
                    result,
                    i,
                    "other errors detected in the message, do you really want to go ahead?",
                )
                continue

            # --- Execute the command ---
            command, execution_error = self._execute_single_command(result)

            # --- Update Status ---
            cmd_key = f"{result.command_name}_{i}"
            line_num = (
                result.errors[0].line_number if result.errors else None
            )  # Should be None here

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

    def _execute_single_command(
        self, result: ParseResult
    ) -> Tuple[Optional[Command], Optional[Exception]]:
        """Execute a single command and return the command object and any execution error."""
        command_name = result.command_name
        args = result.args
        error = None
        command = None

        try:
            registry = CommandRegistry()
            command = registry.get_command(command_name)

            if not command:
                # This should ideally be caught during parsing, but handle defensively
                raise ValueError(f"Command '{command_name}' not found in registry.")

            if (
                not self.engine.is_root_problem_defined()
                and command_name != "define_problem"
            ):
                raise ValueError(
                    "Only 'define_problem' command is allowed before a problem is defined."
                )

            # Update command context before execution
            self.command_context.refresh_from_engine()

            # Execute the command
            command.execute(self.command_context, args)

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
            if (
                self._parsing_error_report
                and "### Errors report:" in self._parsing_error_report
            ):
                self.final_error_report += "\n---\n" + execution_report
            else:  # Only execution errors or syntax errors
                self.final_error_report += "\n" + execution_report

    def _update_auto_reply(self):
        """Add error reports and confirmation requests to the auto-reply aggregator."""
        auto_reply_generator = self.chat_history.get_auto_reply_aggregator(
            self._current_history_tag
        )

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
            if (
                "### Errors report:" not in self.final_error_report
                and "### Execution Status Report:" not in self.final_error_report
            ):
                report_to_add = "### Errors report:\n" + self.final_error_report
            else:
                report_to_add = self.final_error_report
            auto_reply_generator.add_error_report(report_to_add)


class DeepResearchEngine:
    """Core engine for Deep Research functionality, independent of UI implementation"""

    def __init__(
        self,
        root_dir: str = "research",
        llm_interface: LLMInterface = None,
        extension_commands: List = None,
    ):
        self.file_system = FileSystem(root_dir)
        self.chat_history = ChatHistory()
        self.command_parser = CommandParser()
        self.finished = False
        self.logger = DeepResearchLogger(Path(root_dir))
        self.llm_interface = llm_interface
        self.current_node: Optional[Node] = None
        self.next_node: Optional[Node] = None  # Tracks scheduled focus changes
        self.revision_index = 1

        # Check if problem already exists
        self.file_system.load_existing_problem()

        # TODO: Could move to the file system
        self.permanent_log = []

        # Create command context for commands to use - shared across all commands
        self.command_context = CommandContext(self)

        # Set current node to root node if problem is already defined
        if self.is_root_problem_defined():
            self.manually_choose_and_activate_node()

        # Register any extension commands
        if extension_commands:
            for command_class in extension_commands:
                CommandRegistry().register(command_class())

        self._extension_commands = extension_commands

        # Update interface with the file system
        self.interface = DeepResearcherInterface(self.file_system)

        # Print initial status
        self._print_current_status()

    def is_root_problem_defined(self) -> bool:
        """Check if the root problem is already defined"""
        return self.file_system.root_node is not None

    def define_root_problem(self, instruction: str) -> bool:
        """
        Handle the initial problem definition phase.

        Returns:
            bool: True if a problem was successfully defined, False otherwise
        """
        # Check if LLM interface is available
        if not self.llm_interface:
            raise ValueError("LLM interface is required for execution")

        title = instruction[:200]
        if len(instruction) > 200:
            title += "..."
        self.file_system.create_root_problem("User Request: " + title, instruction)

        self.activate_node(self.file_system.root_node)
        self._print_current_status()
        return True

    def execute(self) -> str:
        """
        Execute the deep research process after the root problem is defined and return the final report.

        Returns:
            str: Final report
        """
        # Check if LLM interface is available
        if not self.llm_interface:
            raise ValueError("LLM interface is required for execution")

        # Check if root problem is defined
        if not self.is_root_problem_defined():
            raise ValueError("Root problem must be defined before execution")

        initial_interface_content_by_node = defaultdict()

        while not self.finished:
            # Get the interface content - now returns static content and a list of dynamic sections
            static_interface_content, dynamic_sections = (
                self.interface.render_problem_defined(
                    self.current_node, self.permanent_log
                )
            )

            if self._current_history_tag not in initial_interface_content_by_node or not initial_interface_content_by_node[self._current_history_tag]:
                initial_interface_content_by_node[self._current_history_tag] = "\n\n".join([
                    static_interface_content,
                    *dynamic_sections
                ])

            # Update auto reply aggregator with the new dynamic sections
            current_auto_reply_aggregator = self.chat_history.get_auto_reply_aggregator(
                self._current_history_tag
            )
            current_auto_reply_aggregator.update_dynamic_sections(dynamic_sections)

            # Convert history messages to dict format for the LLM interface
            history_messages = []

            auto_reply_counter = 0
            auto_reply_max_length = None

            current_auto_reply = self.chat_history.commit_and_get_auto_reply(
                self._current_history_tag
            )

            if current_auto_reply:
                print(current_auto_reply.generate_auto_reply())

            for block in self.chat_history.get_compiled_blocks(
                self._current_history_tag
            )[::-1]:  # Reverse to handle auto reply contraction
                if isinstance(block, ChatMessage):
                    history_messages.append(
                        {"author": block.author, "content": block.content}
                    )
                elif isinstance(block, AutoReply):
                    auto_reply_counter += 1

                    if auto_reply_counter > 1:
                        if not auto_reply_max_length:
                            auto_reply_max_length = 5_000
                        else:
                            auto_reply_max_length = max(
                                auto_reply_max_length // 2, 300
                            )
                    history_messages.append(
                        {
                            "author": "user",
                            "content": block.generate_auto_reply(
                                auto_reply_max_length
                            ),
                        }
                    )

            history_messages = history_messages[
                ::-1
            ]  # Reverse to maintain chronological order

            # Get the current node path for logging
            current_node_path = (
                self.current_node.path
                if self.current_node
                else self.file_system.root_dir
            )

            # Generate the request
            request = self.llm_interface.generate_request(
                initial_interface_content_by_node[self._current_history_tag],
                history_messages,
                current_node_path,
            )

            # Process the request and get the response
            response_generator = self._handle_llm_request(request, current_node_path)

            # Get the full response
            try:
                full_llm_response = next(response_generator)
            except StopIteration:
                full_llm_response = ""

            # Process the commands in the response
            self.process_commands(full_llm_response)

            # Apply any scheduled focus change now that the cycle is complete
            if self.next_node is not None:
                self.activate_node(self.next_node)
                self.next_node = None

            self._print_current_status()

        # Generate the final report
        return self._generate_final_report()

    def manually_choose_and_activate_node(self):
        all_nodes = self.file_system.get_all_nodes()
        for index, node in enumerate(all_nodes):
            print(f"{'*' * (node.depth_from_root + 1)} {index+1}: {node.title}")
        print()

        index = None
        while index is None:
            try:
                index = int(input("Choose the node to start from: "))
            except ValueError:
                print("Invalid input. Please enter a number.")
            if not index or index <= 0 or index > len(all_nodes):
                print("Invalid index. Please try again.")
                index = None

        index -= 1
        node = all_nodes[index]
        self.activate_node(node)

    def add_command_output(
        self, command_name: str, args: Dict, output: str, node_title: str
    ) -> None:
        """
        Add command output to be included in the automatic response

        Args:
            command_name: Name of the command
            args: Arguments passed to the command
            output: Output text to display
            node_title: The title of the node for which the output is being added
        """
        if not output:
            output = ""
        auto_reply_aggregator = self.chat_history.get_auto_reply_aggregator(node_title)
        auto_reply_aggregator.add_command_output(
            command_name, {"args": args, "output": output}
        )

    def process_commands(self, text: str) -> tuple[bool, str, Dict]:
        """
        Process commands from text using the _CommandProcessor helper class.

        Returns:
            tuple: (commands_executed, error_report, execution_status)
        """
        processor = _CommandProcessor(self)
        return processor.process(text)

    @property
    def _current_history_tag(self):
        if self.current_node:
            return self.current_node.title
        else:
            return "no_node"

    def _print_current_status(self):
        """Print the current status of the research to STDOUT"""
        status_printer = StatusPrinter()
        status_printer.print_status(
            self.is_root_problem_defined(), self.current_node, self.file_system
        )

    def activate_node(self, node: Node) -> None:
        """Set the current node and update chat history"""
        self.current_node = node
        node.status = ProblemStatus.IN_PROGRESS

    def increment_revision(self):
        self.revision_index += 1

    def _handle_llm_request(self, request, current_node_path):
        """
        Handle the LLM request with retry capability

        Args:
            request: Request object to send to LLM
            current_node_path: Path to current node for logging

        Returns:
            Generator yielding the full response
        """
        while True:
            try:
                response_generator = self.llm_interface.send_request(request)

                # Get the full response
                try:
                    full_llm_response = next(response_generator)
                    # Log the response
                    self.llm_interface.log_response(
                        current_node_path, full_llm_response
                    )
                    yield full_llm_response
                    break  # Successfully got a response, exit the retry loop
                except StopIteration:
                    full_llm_response = ""
                    yield full_llm_response
                    break  # Empty response but not an error, exit the retry loop
            except Exception:
                import traceback

                print("\n\n===== LLM INTERFACE ERROR =====")
                print(traceback.format_exc())
                print("===============================")
                print("\nPress Enter to retry or Ctrl+C to exit...")
                try:
                    input()  # Wait for user input
                    print("Retrying LLM request...")
                except KeyboardInterrupt:
                    print("\nExiting due to user request.")
                    yield "Research terminated due to LLM interface error."
                    break

    def _generate_final_report(self) -> str:
        """Generate a summary of all artifacts created during the research"""
        report_generator = ReportGenerator(self.file_system)
        return report_generator.generate_final_report(self.interface)

    def focus_down(self, subproblem_title: str) -> bool:
        """
        Schedule focus down to a subproblem after the current cycle is complete

        Args:
            subproblem_title: Title of the subproblem to focus on

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_node:
            return False

        # Check if the subproblem exists
        if subproblem_title not in self.current_node.subproblems:
            return False

        # Get the subproblem
        subproblem = self.current_node.subproblems[subproblem_title]

        # Set the parent to PENDING
        self.current_node.status = ProblemStatus.PENDING

        # Schedule the focus change
        self.next_node = subproblem

        # Update files
        self.file_system.update_files()

        return True

    def focus_up(self) -> bool:
        """
        Schedule focus up to the parent problem after the current cycle is complete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_node:
            return False

        # Get the parent chain
        parent_chain = self.file_system.get_parent_chain(self.current_node)

        # If this is the root node, we're done
        if len(parent_chain) <= 1:
            # Mark the root node as FINISHED
            self.current_node.status = ProblemStatus.FINISHED
            self.file_system.update_files()
            self.finished = True
            return True

        # Mark the current node as FINISHED
        self.current_node.status = ProblemStatus.FINISHED
        current_node = self.current_node

        # Get the parent node (second to last in the chain, as the last is the current node)
        parent_node = parent_chain[-2]

        # Schedule the focus change
        self.next_node = parent_node

        # Update files
        self.file_system.update_files()

        parent_auto_reply_aggregator = self.chat_history.get_auto_reply_aggregator(
            parent_node.title
        )
        parent_auto_reply_aggregator.add_internal_message_from(
            "Task marked FINISHED, focusing back up.", current_node.title
        )

        return True

    def fail_and_focus_up(self) -> bool:
        """
        Mark the current problem as failed and schedule focus up after the current cycle is complete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_node:
            return False

        # Get the parent chain
        parent_chain = self.file_system.get_parent_chain(self.current_node)

        # If this is the root node, we're done
        if len(parent_chain) <= 1:
            # Mark the root node as FAILED
            self.current_node.status = ProblemStatus.FAILED
            self.file_system.update_files()
            self.finished = True
            return True

        # Mark the current node as FAILED
        self.current_node.status = ProblemStatus.FAILED
        current_node = self.current_node

        # Get the parent node (second to last in the chain, as the last is the current node)
        parent_node = parent_chain[-2]

        # Schedule the focus change
        self.next_node = parent_node

        # Update files
        self.file_system.update_files()

        parent_auto_reply_aggregator = self.chat_history.get_auto_reply_aggregator(
            parent_node.title
        )
        parent_auto_reply_aggregator.add_internal_message_from(
            "Task marked FAILED, focusing back up.", current_node.title
        )

        return True
