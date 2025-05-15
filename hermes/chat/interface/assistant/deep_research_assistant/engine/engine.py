from collections import defaultdict
from pathlib import Path

# Import the specific context for Deep Research
from hermes.chat.interface.assistant.deep_research_assistant.engine.commands.command_context import (
    CommandContext,
)

# Import the registry creation function and type alias
from hermes.chat.interface.assistant.deep_research_assistant.engine.context.dynamic_sections.registry import (
    DynamicDataTypeToRendererMap,
    get_data_type_to_renderer_instance_map,
    register_all_dynamic_section_types,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.context.interface import (
    DeepResearcherInterface,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.report.report_generator import (
    ReportGenerator,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.report.status_printer import (
    StatusPrinter,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research import Research, ResearchNode
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research import ResearchImpl
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node import ResearchNodeImpl
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.history.history_blocks import (
    AutoReply,
    ChatMessage,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemStatus,
)

# Import other necessary components
from hermes.chat.interface.assistant.deep_research_assistant.engine.state_machine import StateMachineNode
from hermes.chat.interface.assistant.deep_research_assistant.engine.state_machine.state_machine import StateMachineImpl
from hermes.chat.interface.assistant.deep_research_assistant.llm_interface import (
    LLMInterface,
)

# Import core command components from the new location
from hermes.chat.interface.commands.command import (
    Command,
    CommandRegistry,
)
from hermes.chat.interface.commands.command_parser import CommandParser, ParseResult
from hermes.chat.interface.commands.help_generator import CommandHelpGenerator
from hermes.chat.interface.templates.template_manager import TemplateManager


class _CommandProcessor:
    """Helper class to encapsulate command processing logic."""

    def __init__(self, engine: "DeepResearchEngine"):
        self.engine = engine
        self.command_parser = engine.command_parser

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
            # Use the singleton registry instance directly
            registry = CommandRegistry()
            # Cast the retrieved command to the specific type expected
            command = registry.get_command(command_name)  # type: ignore

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


class DeepResearchEngine:
    """Core engine for Deep Research functionality, independent of UI implementation"""

    research: Research

    def __init__(
        self,
        root_dir: Path,
        llm_interface: LLMInterface,
    ):
        # Register all dynamic section types immediately
        register_all_dynamic_section_types()

        # Use the templates directory from the Deep Research Assistant package
        templates_dir = Path(__file__).parent / "templates"
        self.template_manager = TemplateManager(templates_dir)

        self.renderer_registry: DynamicDataTypeToRendererMap = get_data_type_to_renderer_instance_map(self.template_manager)

        # Initialize the research object which will handle all file system and node operations
        self.research = ResearchImpl(root_dir)
        self.state_machine = StateMachineImpl()

        # Initialize other components
        self.command_parser = CommandParser()
        # Legacy logger - will be fully removed in future versions
        self.llm_interface = llm_interface
        # When parent requests activation of multiple children sequentially, we'll track them here
        # Then when the child is finished, and wants to activate the parent again, we'll activate the next in the queue
        # It's a dict, as the child itself might activate other grandchildren
        self.children_queue = defaultdict(list)  # Queue for activating siblings sequentially

        # Budget tracking
        self.budget: int | None = None  # No budget by default
        self.initial_budget = None  # Store the initial budget for reference
        self.message_cycles_used = 0
        self.budget_warning_shown = False

        self.root_completion_message: str | None = None  # To store the final message from the root node

        if self.research.research_already_exists():
            self.research.load_existing_research()
            self.state_machine.set_root_research_node(self.research.get_root_node())

        commands_help_generator = CommandHelpGenerator()
        # Update interface to use the research object
        self.interface = DeepResearcherInterface(self.research, self.template_manager, commands_help_generator)

    def is_root_problem_defined(self) -> bool:
        """Check if the root problem is already defined"""
        return self.research.research_initiated()

    def define_root_problem(self, instruction: str):
        """
        Handle the initial problem definition phase.

        Returns:
            bool: True if a problem was successfully defined, False otherwise
        """
        title = instruction[:200]
        if len(instruction) > 200:
            title += "..."

        problem_definition = ProblemDefinition(content=instruction)
        node = ResearchNodeImpl(problem=problem_definition, title=title, path=self.research.get_root_directory(), parent=None)
        self.research.initiate_research(node)
        self.state_machine.set_root_research_node(self.research.get_root_node())

        self._print_current_status(self.research.get_root_node())

    def add_new_instruction(self, instruction: str):
        """Injects a new user instruction into the current node's context."""
        if not self.research.research_initiated():
            print("Error: Cannot prepare for new instruction without an active node.")
            return

        print(f"Preparing node '{self.research.get_root_node().get_title()}' for new instruction.")
        # Format the instruction using the template
        formatted_instruction = self.template_manager.render_template("context/new_user_instruction.mako", instruction=instruction)

        # Add the formatted instruction as an internal message to the current node's auto-reply
        root_node = self.research.get_root_node()
        history = root_node.get_history()
        auto_reply_aggregator = history.get_auto_reply_aggregator()
        auto_reply_aggregator.add_internal_message_from(formatted_instruction, "USER MESSAGE")

        # Mark the root problem as in progress
        root_node.set_problem_status(ProblemStatus.IN_PROGRESS)
        self.state_machine.reactivate_root_node(root_node)

        print("Engine ready to execute new instruction.")

    def execute(self) -> None:
        """
        Execute the deep research process. Runs until the current task is completed
        (node finished/failed and focus returns to root, or budget exhausted, or shutdown).
        """
        # Check if root problem is defined
        if not self.is_root_problem_defined():
            raise ValueError("Root problem must be defined before execution")

        should_finish = False

        while True:
            # Get the next node from the state machine - this should be the ONLY call to next() per cycle
            current_state_machine_node = self.state_machine.next()
            if current_state_machine_node is None:
                break

            research_node = current_state_machine_node.get_research_node()

            if not self.research.research_initiated():
                print("Error: No active node during execution loop. Stopping.")
                break

            # --- 1. Gather Current Interface State ---
            # Get static content and the *data* for dynamic sections
            static_interface_content, current_dynamic_data = self.interface.render_problem_defined(
                research_node,
                self.research.get_permanent_logs().get_logs(),
                self.budget,
                self.get_remaining_budget(),
            )

            # Get the current node's history
            node_history = research_node.get_history()

            # Store the initial full interface view if not already done for this node
            if not node_history.get_initial_interface_content():
                # Render the initial dynamic sections *without* future changes for the first message
                initial_rendered_dynamics = []
                for data_instance in current_dynamic_data:
                    renderer = self.renderer_registry.get(type(data_instance))
                    if renderer:
                        # Render with future_changes=0 for the initial static view
                        initial_rendered_dynamics.append(renderer.render(data_instance, 0))
                    else:
                        initial_rendered_dynamics.append(f"<error>Missing renderer for {type(data_instance).__name__}</error>")

                initial_interface_content = "\n\n".join(
                    [static_interface_content] + initial_rendered_dynamics
                )

                # Store in the node's history
                node_history.set_initial_interface_content(initial_interface_content)

            # --- 2. Update History & Auto-Reply Aggregator ---
            history = research_node.get_history()
            current_auto_reply_aggregator = history.get_auto_reply_aggregator()
            # Compare current data with last state and update aggregator's list of *changed* sections
            current_auto_reply_aggregator.update_dynamic_sections(current_dynamic_data)

            # Commit changes (errors, commands, messages, changed sections) to a new AutoReply block
            # This clears the aggregator for the next cycle.
            history = research_node.get_history()
            current_auto_reply_block = history.commit_and_get_auto_reply()

            # --- 3. Prepare History for LLM (Render Auto-Replies) ---
            history_messages = []
            compiled_blocks = research_node.get_history().get_compiled_blocks()
            auto_reply_counter = 0
            auto_reply_max_length = 5000

            for i in range(len(compiled_blocks) - 1, -1, -1):
                block = compiled_blocks[i]
                if isinstance(block, ChatMessage):
                    history_messages.append({"author": block.author, "content": block.content})
                elif isinstance(block, AutoReply):
                    auto_reply_counter += 1

                    # --- Calculate Future Changes for this AutoReply ---
                    future_changes_map: dict[int, int] = defaultdict(int)
                    # Look ahead in the *rest* of the compiled blocks
                    for future_block in compiled_blocks[i + 1 :]:
                        if isinstance(future_block, AutoReply):
                            for section_index, _ in future_block.dynamic_sections:
                                future_changes_map[section_index] += 1

                    # --- Apply Auto-Reply Truncation Logic ---
                    # (This logic might need refinement based on desired behavior)
                    current_max_len = None
                    # Example: Start truncating after 3 auto-replies
                    if auto_reply_counter > 3:
                        current_max_len = auto_reply_max_length
                        auto_reply_max_length = max(auto_reply_max_length // 2, 300)

                    # --- Render the AutoReply block ---
                    # Pass registry, future changes, and truncation length
                    auto_reply_content = block.generate_auto_reply(
                        template_manager=self.template_manager,
                        renderer_registry=self.renderer_registry,
                        future_changes_map=future_changes_map,
                        per_command_output_maximum_length=current_max_len,
                    )
                    history_messages.append(
                        {
                            "author": "user",
                            "content": auto_reply_content,
                        }  # Auto-replies are from 'user' perspective for LLM
                    )

            history_messages = history_messages[::-1]

            # --- 4. Print Latest Auto-Reply to Console (Optional) ---
            # Render the *last* auto-reply added (if any) for console view, without future changes/truncation
            if current_auto_reply_block:
                console_auto_reply = current_auto_reply_block.generate_auto_reply(
                    template_manager=self.template_manager,
                    renderer_registry=self.renderer_registry,
                    future_changes_map={},  # No future changes for console view
                    per_command_output_maximum_length=None,  # No truncation for console
                )
                print(console_auto_reply)

            # Get the current node path for logging
            current_node_path = research_node.get_path()

            # Get the initial interface content from the node's history
            initial_interface_content = research_node.get_history().get_initial_interface_content()
            if not initial_interface_content:
                raise Exception("No initial content, something is wrong, please start a new research")

            # Generate the request
            request = self.llm_interface.generate_request(
                initial_interface_content,
                history_messages,
                current_node_path,
            )

            # Log the request using node logger
            research_node.get_logger().log_llm_request(history_messages, request, initial_interface_content)

            # Process the request and get the response
            response_generator = self._handle_llm_request(request, current_node_path, research_node)

            # Get the full response
            try:
                full_llm_response = next(response_generator)
            except StopIteration:
                full_llm_response = ""

            # Process the commands in the response
            self.process_commands(full_llm_response, current_state_machine_node)

            # Increment message cycles and check budget
            self.increment_message_cycles()

            # Check if budget is exhausted
            if self.is_budget_exhausted():
                assert self.budget is not None

                if not self.budget_warning_shown:
                    self.budget_warning_shown = True
                    print("\n===== BUDGET ALERT =====")
                    print(f"Budget of {self.budget} message cycles has been exhausted.")
                    print(f"Current usage: {self.message_cycles_used} cycles")

                    # Add a buffer of 10 cycles
                    self.budget += 10
                    print(f"Adding a buffer of 10 cycles. New budget: {self.budget}")
                    print("The assistant will be notified to wrap up quickly.")

                    # Add a warning message to the current node's auto reply
                    auto_reply_aggregator = research_node.get_history().get_auto_reply_aggregator()
                    auto_reply_aggregator.add_internal_message_from(
                        "⚠️ BUDGET ALERT: The message cycle budget has been exhausted. "
                        "Please finalize your work as quickly as possible. "
                        "You have a buffer of 10 additional cycles to complete your work.",
                        "SYSTEM",
                    )
                elif self.message_cycles_used >= self.budget:
                    # Buffer is also exhausted
                    print("\n===== BUDGET COMPLETELY EXHAUSTED =====")
                    print(f"Initial budget: {self.initial_budget} cycles")
                    print(f"Current usage: {self.message_cycles_used} cycles (including buffer)")

                    user_input = input("Would you like to add 20 more cycles to continue? (y/N): ").strip().lower()
                    if user_input == "y":
                        additional_cycles = 20
                        self.budget += additional_cycles
                        print(f"Added {additional_cycles} more cycles. New budget: {self.budget}")

                        # Add a notification to the current node's auto reply
                        auto_reply_aggregator = research_node.get_history().get_auto_reply_aggregator()
                        auto_reply_aggregator.add_internal_message_from(
                            f"The budget has been extended with {additional_cycles} additional cycles. "
                            f"New total: {self.budget} cycles.",
                            "SYSTEM",
                        )
                    else:
                        print("Finishing research due to budget constraints. Engine will await new instructions.")
                        should_finish = True
                        # Mark current node as failed? Or just stop? Let's mark as failed.
                        research_node.set_problem_status(ProblemStatus.FAILED)

            # Check if approaching budget limit (within 10 cycles)
            elif self.budget is not None and self.is_approaching_budget_limit() and not self.budget_warning_shown:
                self.budget_warning_shown = True
                print("\n===== BUDGET WARNING =====")
                print(f"Approaching budget limit. {self.get_remaining_budget()} cycles remaining out of {self.budget}.")

                # Add a warning message to the current node's auto reply
                auto_reply_aggregator = research_node.get_history().get_auto_reply_aggregator()
                auto_reply_aggregator.add_internal_message_from(
                    f"⚠️ BUDGET WARNING: Only {self.get_remaining_budget()} message cycles remaining out of {self.budget}. "
                    "Please prioritize the most important tasks and consider wrapping up soon.",
                    "SYSTEM",
                )

            # Ensure the current node's history is saved before potentially changing nodes
            research_node.get_history().save()

            # Check if we should finish this cycle
            if should_finish:
                break

            current_state_machine_node.finish()
            self._print_current_status(current_state_machine_node.get_research_node())

        print("Engine execution cycle complete. Awaiting new instruction.")

    def finish_with_this_cycle(self):
        # No need to set future_execution_state anymore
        # We'll check the should_finish flag locally in the execute method
        pass

    def add_command_output(self, command_name: str, args: dict, output: str, node_title: str, current_state_machine_node: "StateMachineNode") -> None:
        """
        Add command output to be included in the automatic response

        Args:
            command_name: Name of the command
            args: Arguments passed to the command
            output: Output text to display
            node_title: The title of the node for which the output is being added
            current_state_machine_node: The current state machine node (optional, pass from context)
        """
        if not output:
            output = ""

        auto_reply_aggregator = current_state_machine_node.get_research_node().get_history().get_auto_reply_aggregator()
        auto_reply_aggregator.add_command_output(command_name, {"args": args, "output": output})

    def process_commands(self, text: str, current_state_machine_node: "StateMachineNode") -> tuple[bool, str, dict]:
        """
        Process commands from text using the _CommandProcessor helper class.

        Args:
            text: The text containing commands to process
            current_state_machine_node: The current state machine node (optional, pass from context)

        Returns:
            tuple: (commands_executed, error_report, execution_status)
        """
        processor = _CommandProcessor(self)
        return processor.process(text, current_state_machine_node)

    def _print_current_status(self, current_node: 'ResearchNode'):
        """
        Print the current status of the research to STDOUT

        Args:
            current_node: The current research node.
        """
        status_printer = StatusPrinter(self.template_manager)
        # Update to pass research directly
        status_printer.print_status(current_node, self.research)

    def set_budget(self, budget: int, current_state_machine_node: 'StateMachineNode'):
        """
        Set the budget for the Deep Research Assistant

        Args:
            budget: The budget value to set
            current_state_machine_node: The current state machine node.
        """
        self.budget = budget
        self.initial_budget = budget
        self.budget_warning_shown = False

        auto_reply_aggregator = current_state_machine_node.get_research_node().get_history().get_auto_reply_aggregator()
        auto_reply_aggregator.add_internal_message_from(f"Budget has been set to {budget} message cycles.", "SYSTEM")

    def increment_message_cycles(self):
        """Increment the message cycles counter"""
        self.message_cycles_used += 1

    def get_remaining_budget(self):
        """Get the remaining budget"""
        if self.budget is None:
            return None
        return self.budget - self.message_cycles_used

    def is_budget_exhausted(self):
        """Check if the budget is exhausted"""
        if self.budget is None:
            return False
        return self.message_cycles_used >= self.budget

    def is_approaching_budget_limit(self):
        """Check if we're approaching the budget limit (within 10 cycles)"""
        if self.budget is None:
            return False
        remaining = self.get_remaining_budget()
        # Ensure remaining is not None before comparison
        return remaining is not None and 0 < remaining <= 10


    def _handle_llm_request(self, request, current_node_path, research_node):
        """
        Handle the LLM request with retry capability

        Args:
            request: Request object to send to LLM
            current_node_path: Path to current node for logging
            research_node: The current research node

        Returns:
            Generator yielding the full response
        """
        while True:
            try:
                response_generator = self.llm_interface.send_request(request)

                # Get the full response
                try:
                    full_llm_response = next(response_generator)
                    # Log the response using node logger - primary method
                    research_node.get_logger().log_llm_response(full_llm_response)
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
                    yield "Research terminated due to LLM interface error."  # Or re-raise?
                    break

    def _generate_final_report(self) -> str:
        """Generate a summary of all artifacts created during the research. (Currently not called automatically)"""
        report_generator = ReportGenerator(self.research, self.template_manager)
        # Pass the root completion message to the generator
        return report_generator.generate_final_report(self.interface, self.root_completion_message)

    def focus_down(self, subproblem_title: str, current_state_machine_node: 'StateMachineNode') -> bool:
        """
        Schedule focus down to a subproblem after the current cycle is complete

        Args:
            subproblem_title: Title of the subproblem to focus on
            current_state_machine_node: The current state machine node.

        Returns:
            bool: True if successful, False otherwise
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

    def focus_up(self, message: str | None, current_state_machine_node: 'StateMachineNode') -> bool:
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

        # If this is the root node (no parent), we're done
        if parent_node is None:
            # Mark the root node as FINISHED
            current_research_node.set_problem_status(ProblemStatus.FINISHED)
            # Store the completion message if provided
            # Root node finished. Set awaiting flag.
            if message:
                self.root_completion_message = message  # Store final message if any
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
            "Task marked FINISHED, focusing back up.",
            current_research_node.get_title()
        )

        # 2. If a custom message was provided, add it as well
        if message:
            # Prefix the custom message for clarity
            parent_auto_reply_aggregator.add_internal_message_from(
                f"[Completion Message]: {message}",
                current_research_node.get_title()
            )

        # The node will be finished at the end of this cycle
        # State machine will automatically return to parent node via next()

        return True

    def fail_and_focus_up(self, message: str | None, current_state_machine_node: 'StateMachineNode') -> bool:
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

        # If this is the root node (no parent), we're done
        if parent_node is None:
            # Mark the root node as FAILED
            current_research_node.set_problem_status(ProblemStatus.FAILED)
            # Store the failure message if provided
            # Root node failed. Set awaiting flag.
            if message:
                self.root_completion_message = message  # Store final message if any
            print(f"Root node '{current_research_node.get_title()}' failed. Engine awaiting new instruction.")
            return True

        # Mark the current non-root node as FAILED
        current_research_node.set_problem_status(ProblemStatus.FAILED)

        # --- Add messages to parent's auto-reply BEFORE scheduling focus ---
        parent_history = parent_node.get_history()
        parent_auto_reply_aggregator = parent_history.get_auto_reply_aggregator()

        # 1. Always add the standard status message
        parent_auto_reply_aggregator.add_internal_message_from(
            "Task marked FAILED, focusing back up.",
            current_research_node.get_title()
        )

        # 2. If a custom failure message was provided, add it as well
        if message:
            # Prefix the custom message for clarity
            parent_auto_reply_aggregator.add_internal_message_from(
                f"[Failure Message]: {message}",
                current_research_node.get_title()
            )

        # The node will be finished at the end of this cycle
        # State machine will automatically return to parent node via next()

        return True
