from collections import defaultdict
from pathlib import Path
from typing import Generic

from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory, CommandContextType
from hermes.chat.interface.assistant.agent.framework.context import AgentInterface
from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicDataTypeToRendererMap
from hermes.chat.interface.assistant.agent.framework.llm_interface import (
    LLMInterface,
)
from hermes.chat.interface.assistant.agent.framework.report import ReportGenerator
from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent.framework.research.research import ResearchImpl
from hermes.chat.interface.assistant.agent.framework.research.research_node import ResearchNodeImpl
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.history.history_blocks import (
    AutoReply,
    ChatMessage,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode
from hermes.chat.interface.assistant.agent.framework.task_tree.task_tree import TaskTreeImpl
from hermes.chat.interface.assistant.agent.framework.status_printer import StatusPrinter
from hermes.chat.interface.commands.command import CommandRegistry
from hermes.chat.interface.commands.command_parser import CommandParser
from hermes.chat.interface.templates.template_manager import TemplateManager


class AgentEngine(Generic[CommandContextType]):
    """Core engine for Deep Research functionality, independent of UI implementation"""

    research: Research

    def __init__(
        self,
        root_dir: Path,
        llm_interface: LLMInterface,
        command_registry: CommandRegistry,
        command_context_factory: CommandContextFactory[CommandContextType],
        template_manager: TemplateManager,
        renderer_registry: DynamicDataTypeToRendererMap,
        agent_interface: AgentInterface,
        report_generator: ReportGenerator,
        status_printer: StatusPrinter
    ):
        self.command_context_factory = command_context_factory
        self.template_manager = template_manager
        self.renderer_registry = renderer_registry
        self.interface = agent_interface
        self.report_generator = report_generator
        self.status_printer = status_printer

        # Initialize the research object which will handle all file system and node operations
        self.research = ResearchImpl(root_dir)
        self.task_tree = TaskTreeImpl()
        self.command_registry = command_registry

        # Initialize other components
        self.command_parser = CommandParser(self.command_registry)
        self.llm_interface = llm_interface

        # Budget tracking
        self.budget: int | None = None  # No budget by default
        self.message_cycles_used = 0
        self.budget_warning_shown = False

        self.root_completion_message: str | None = None  # To store the final message from the root node

        if self.research.research_already_exists():
            self.research.load_existing_research()
            self.task_tree.set_root_research_node(self.research.get_root_node())

    def is_research_initiated(self) -> bool:
        """Check if the research is already initiated"""
        return self.research.is_research_initiated()

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
        self.task_tree.set_root_research_node(self.research.get_root_node())

        self._print_current_status(self.research.get_root_node())

    def add_new_instruction(self, instruction: str):
        """Injects a new user instruction into the current node's context."""
        if not self.research.is_research_initiated():
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
        self.task_tree.reactivate_root_node(root_node)

        print("Engine ready to execute new instruction.")

    def execute(self) -> None:
        """
        Execute the deep research process. Runs until the current task is completed
        (node finished/failed and focus returns to root, or budget exhausted, or shutdown).
        """
        # Check if root problem is defined
        if not self.is_research_initiated():
            raise ValueError("Root problem must be defined before execution")

        self._should_finish = False
        current_state_machine_node = None

        while not self._should_finish:
            if (not current_state_machine_node
                    or current_state_machine_node.is_finished()
                    or current_state_machine_node.has_pending_children()):
                current_state_machine_node = self.task_tree.next()
                if current_state_machine_node is None:
                    break

            research_node = current_state_machine_node.get_research_node()

            if not self.research.is_research_initiated():
                print("Error: No active node during execution loop. Stopping.")
                break

            # --- 1. Gather Current Interface State ---
            # Get static content and the *data* for dynamic sections
            static_interface_content, current_dynamic_data = self.interface.render_problem_defined(
                self.research,
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
                        self._should_finish = True
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

            self._print_current_status(current_state_machine_node.get_research_node())

        print("Engine execution cycle complete. Awaiting new instruction.")

    def emergency_shutdown(self):
        self._should_finish = True

    def add_command_output(
        self, command_name: str, args: dict, output: str, node_title: str, current_state_machine_node: "TaskTreeNode"):
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

    def process_commands(self, text: str, current_state_machine_node: "TaskTreeNode") -> tuple[bool, str, dict]:
        """
        Process commands from text using the CommandProcessor helper class.

        Args:
            text: The text containing commands to process
            current_state_machine_node: The current state machine node (optional, pass from context)

        Returns:
            tuple: (commands_executed, error_report, execution_status)
        """
        processor = CommandProcessor(self, self.command_registry, self.command_context_factory)
        return processor.process(text, current_state_machine_node)

    def _print_current_status(self, current_node: 'ResearchNode'):
        """
        Print the current status of the research to STDOUT

        Args:
            current_node: The current research node.
        """
        self.status_printer.print_status(current_node, self.research)

    def set_budget(self, budget: int):
        """
        Set the budget for the Deep Research Assistant

        Args:
            budget: The budget value to set
            current_state_machine_node: The current state machine node.
        """
        self.budget = budget
        self.budget_warning_shown = False

        # TODO: Show information about increase of budget in a shared system information

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
        return self.report_generator.generate_final_report(self.research, self.interface, self.root_completion_message)

    def focus_down(self, subproblem_title: str, current_state_machine_node: 'TaskTreeNode') -> bool:
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

    def focus_up(self, message: str | None, current_state_machine_node: 'TaskTreeNode') -> bool:
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

    def fail_and_focus_up(self, message: str | None, current_state_machine_node: 'TaskTreeNode') -> bool:
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
