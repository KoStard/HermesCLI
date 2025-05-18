from collections import defaultdict
from pathlib import Path
from typing import Generic

from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory, CommandContextType
from hermes.chat.interface.assistant.agent.framework.context import AgentInterface
from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicDataTypeToRendererMap
from hermes.chat.interface.assistant.agent.framework.engine_processing_state import EngineProcessingState
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
from hermes.chat.interface.assistant.agent.framework.status_printer import StatusPrinter
from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode
from hermes.chat.interface.assistant.agent.framework.task_tree.task_tree import TaskTreeImpl
from hermes.chat.interface.commands.command import CommandRegistry
from hermes.chat.interface.commands.command_parser import CommandParser
from hermes.chat.interface.templates.template_manager import TemplateManager


class AgentEngine(Generic[CommandContextType]):
    """Core engine for Deep Research functionality, independent of UI implementation"""

    research: Research
    # _should_finish: bool # This will be part of EngineProcessingState or local to execute
    # root_completion_message: str | None # This will be part of EngineProcessingState

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
        self.final_root_completion_message: str | None = None


        # self.root_completion_message: str | None = None # Replaced by state management

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

    def _create_and_add_new_instruction_message(self, instruction: str, root_node: ResearchNode):
        """Formats the instruction and adds it to the root node's history."""
        formatted_instruction = self.template_manager.render_template(
            "context/new_user_instruction.mako", instruction=instruction
        )
        history = root_node.get_history()
        auto_reply_aggregator = history.get_auto_reply_aggregator()
        auto_reply_aggregator.add_internal_message_from(formatted_instruction, "USER MESSAGE")

    def add_new_instruction(self, instruction: str):
        """Injects a new user instruction into the current node's context."""
        if not self.research.is_research_initiated():
            print("Error: Cannot prepare for new instruction without an active node.")
            return

        root_node = self.research.get_root_node()
        print(f"Preparing node '{root_node.get_title()}' for new instruction.")

        self._create_and_add_new_instruction_message(instruction, root_node)

        # Mark the root problem as in progress
        root_node.set_problem_status(ProblemStatus.IN_PROGRESS)
        self.task_tree.reactivate_root_node(root_node)

        print("Engine ready to execute new instruction.")

    def execute(self) -> None:
        """
        Execute the deep research process. Runs until the current task is completed
        (node finished/failed and focus returns to root, or budget exhausted, or shutdown).
        """
        if not self.is_research_initiated():
            raise ValueError("Root problem must be defined before execution")

        # This variable will be managed by the loop, derived from EngineProcessingState
        # self._should_finish is effectively replaced by current_engine_state.should_finish

        current_engine_state = EngineProcessingState() # Initial state for the execution run
        current_state_machine_node = None

        while not current_engine_state.should_finish: # Loop controlled by state
            # --- Task Tree Node Selection ---
            if (not current_state_machine_node
                    or current_state_machine_node.is_finished()
                    or current_state_machine_node.has_pending_children()):
                current_state_machine_node = self.task_tree.next()
                if current_state_machine_node is None: # All tasks done
                    current_engine_state = current_engine_state.with_should_finish(True)
                    break

            research_node = current_state_machine_node.get_research_node()

            # --- Interface Rendering & History Preparation ---
            static_interface_content, current_dynamic_data = self._prepare_interface_and_history_for_node(research_node)

            history_messages = self._compile_history_for_llm(research_node)

            initial_interface_content = research_node.get_history().get_initial_interface_content()
            if not initial_interface_content: # Should have been set by _prepare_interface_and_history_for_node
                raise Exception("No initial content after prep, something is wrong.")

            # --- LLM Interaction ---
            llm_request = self.llm_interface.generate_request(
                initial_interface_content, history_messages, research_node.get_path()
            )
            research_node.get_logger().log_llm_request(history_messages, llm_request, initial_interface_content)

            full_llm_response = self._handle_llm_request(llm_request, research_node.get_path(), research_node)

            # --- Command Processing ---
            # Pass the current_engine_state to process_commands, which returns a new state
            current_engine_state = self.process_commands(full_llm_response, current_state_machine_node, current_engine_state)

            # Update auto-reply based on command processing results (report, etc.)
            # This logic was previously in CommandProcessor._update_auto_reply, called by process()
            # It needs access to current_engine_state.report_this_turn and other flags.
            # For now, let's assume CommandProcessor's process method updates the auto-reply aggregator directly.
            # This is consistent with its _update_auto_reply method.

            # --- Budget Management ---
            self.increment_message_cycles()
            budget_finish_signal = self._manage_budget(research_node)
            if budget_finish_signal:
                current_engine_state = current_engine_state.with_should_finish(True)
                # If budget caused finish, ensure problem status is FAILED
                if research_node.get_problem_status() not in [ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED]:
                    research_node.set_problem_status(ProblemStatus.FAILED)


            # --- Post-Cycle Operations ---
            research_node.get_history().save()
            self._print_current_status(research_node)

            # If engine is flagged to finish (e.g. by budget, shutdown, or root task completion from commands)
            if current_engine_state.should_finish:
                break

        # After loop: current_engine_state.root_completion_message holds the message if any
        # Use this for the final report.
        self.final_root_completion_message = current_engine_state.root_completion_message
        print("Engine execution cycle complete. Awaiting new instruction.")


    def _prepare_interface_and_history_for_node(self, research_node: ResearchNode):
        """Gathers current interface state and updates history for the given node."""
        static_interface_content, current_dynamic_data = self.interface.render_problem_defined(
            self.research,
            research_node,
            self.research.get_permanent_logs().get_logs(),
            self.budget,
            self.get_remaining_budget(),
        )
        node_history = research_node.get_history()
        if not node_history.get_initial_interface_content():
            initial_rendered_dynamics = []
            for data_instance in current_dynamic_data:
                renderer = self.renderer_registry.get(type(data_instance))
                if renderer:
                    initial_rendered_dynamics.append(renderer.render(data_instance, 0))
                else:
                    initial_rendered_dynamics.append(f"<error>Missing renderer for {type(data_instance).__name__}</error>")
            initial_interface_content = "\n\n".join([static_interface_content] + initial_rendered_dynamics)
            node_history.set_initial_interface_content(initial_interface_content)

        current_auto_reply_aggregator = node_history.get_auto_reply_aggregator()
        current_auto_reply_aggregator.update_dynamic_sections(current_dynamic_data)
        node_history.commit_and_get_auto_reply() # This clears aggregator for next cycle

        return static_interface_content, current_dynamic_data

    def _compile_history_for_llm(self, research_node: ResearchNode) -> list[dict]:
        """Compiles and renders historical messages for LLM input."""
        history_messages = []
        compiled_blocks = research_node.get_history().get_compiled_blocks()
        auto_reply_counter = 0
        auto_reply_max_length = 5000 # TODO: Make configurable

        for i in range(len(compiled_blocks) - 1, -1, -1):
            block = compiled_blocks[i]
            if isinstance(block, ChatMessage):
                history_messages.append({"author": block.author, "content": block.content})
            elif isinstance(block, AutoReply):
                auto_reply_counter += 1
                future_changes_map: dict[int, int] = defaultdict(int)
                for future_block in compiled_blocks[i + 1:]:
                    if isinstance(future_block, AutoReply):
                        for section_index, _ in future_block.dynamic_sections:
                            future_changes_map[section_index] += 1

                current_max_len = None
                if auto_reply_counter > 3: # Example truncation logic
                    current_max_len = auto_reply_max_length
                    auto_reply_max_length = max(auto_reply_max_length // 2, 300)

                auto_reply_content = block.generate_auto_reply(
                    template_manager=self.template_manager,
                    renderer_registry=self.renderer_registry,
                    future_changes_map=future_changes_map,
                    per_command_output_maximum_length=current_max_len,
                )
                history_messages.append({"author": "user", "content": auto_reply_content})

        return history_messages[::-1]

    def _render_auto_reply_block_for_llm(
        self,
        block: AutoReply,
        compiled_blocks: list,
        current_block_index: int,
        auto_reply_counter: int, # For potential future use if logic depends on overall count
        auto_reply_max_length: int, # Current max length for this specific block
    ) -> str:
        """Renders a single AutoReply block for LLM history, handling future changes and truncation."""
        future_changes_map: dict[int, int] = defaultdict(int)
        for future_block in compiled_blocks[current_block_index + 1:]:
            if isinstance(future_block, AutoReply):
                for section_index, _ in future_block.dynamic_sections:
                    future_changes_map[section_index] += 1

        # Example truncation logic: use current_max_len passed by a caller if needed, or apply default.
        # The existing logic applies truncation based on auto_reply_counter handled in the caller.
        # This simplified version just uses the passed auto_reply_max_length.
        current_max_len = auto_reply_max_length

        return block.generate_auto_reply(
            template_manager=self.template_manager,
            renderer_registry=self.renderer_registry,
            future_changes_map=future_changes_map,
            per_command_output_maximum_length=current_max_len,
        )

    def _compile_history_for_llm(self, research_node: ResearchNode) -> list[dict]:
        """Compiles and renders historical messages for LLM input."""
        history_messages = []
        compiled_blocks = research_node.get_history().get_compiled_blocks()
        auto_reply_counter = 0
        # Initialize auto_reply_max_length; it will be adjusted inside the loop if needed.
        # This value is used for the *next* auto-reply if truncation is triggered.
        # For the *current* auto-reply, current_max_len is determined first.
        iterative_auto_reply_max_length = 5000 # TODO: Make configurable

        for i in range(len(compiled_blocks) - 1, -1, -1):
            block = compiled_blocks[i]
            if isinstance(block, ChatMessage):
                history_messages.append({"author": block.author, "content": block.content})
            elif isinstance(block, AutoReply):
                auto_reply_counter += 1

                current_max_len_for_this_block = None # Default to no truncation
                if auto_reply_counter > 3: # Example truncation logic
                    current_max_len_for_this_block = iterative_auto_reply_max_length
                    # Adjust max length for subsequent auto-replies
                    iterative_auto_reply_max_length = max(iterative_auto_reply_max_length // 2, 300)

                auto_reply_content = self._render_auto_reply_block_for_llm(
                    block,
                    compiled_blocks,
                    i, # current_block_index
                    auto_reply_counter,
                    current_max_len_for_this_block, # Pass calculated max length for this block
                )
                history_messages.append({"author": "user", "content": auto_reply_content})

        return history_messages[::-1]

    def _handle_budget_exhaustion(self, research_node: ResearchNode) -> bool:
        """Handles logic when budget (including buffer) is fully exhausted. Returns True if research should finish."""
        assert self.budget is not None # Should only be called if budget is set and exhausted
        print("\n===== BUDGET COMPLETELY EXHAUSTED =====")
        print(f"Current usage: {self.message_cycles_used} cycles (including buffer if any)")
        user_input = input("Would you like to add 20 more cycles to continue? (y/N): ").strip().lower()
        if user_input == "y":
            additional_cycles = 20
            self.budget += additional_cycles
            print(f"Added {additional_cycles} more cycles. New budget: {self.budget}")
            research_node.get_history().get_auto_reply_aggregator().add_internal_message_from(
                f"The budget has been extended with {additional_cycles} additional cycles. "
                f"New total: {self.budget} cycles.",
                "SYSTEM",
            )
            return False # Continue with extended budget
        else:
            print("Finishing research due to budget constraints. Engine will await new instructions.")
            return True # Signal to finish

    def _handle_initial_budget_depletion(self, research_node: ResearchNode) -> None:
        """Handles logic when budget is first hit, adds a buffer."""
        assert self.budget is not None
        self.budget_warning_shown = True # Mark that the initial depletion and buffer addition has occurred.
        print("\n===== BUDGET ALERT =====")
        print(f"Budget of {self.budget} message cycles has been exhausted.")

        buffer_cycles = 10
        self.budget += buffer_cycles
        print(f"Adding a buffer of {buffer_cycles} cycles. New budget: {self.budget}")
        print("The assistant will be notified to wrap up quickly.")
        research_node.get_history().get_auto_reply_aggregator().add_internal_message_from(
            f"⚠️ BUDGET ALERT: The message cycle budget has been exhausted. "
            f"A buffer of {buffer_cycles} additional cycles has been added to complete your work. "
            "Please finalize your work as quickly as possible.",
            "SYSTEM",
        )

    def _handle_approaching_budget_warning(self, research_node: ResearchNode) -> None:
        """Handles logic when nearing the budget limit."""
        self.budget_warning_shown = True
        print("\n===== BUDGET WARNING =====")
        print(f"Approaching budget limit. {self.get_remaining_budget()} cycles remaining out of {self.budget}.")
        research_node.get_history().get_auto_reply_aggregator().add_internal_message_from(
            f"⚠️ BUDGET WARNING: Only {self.get_remaining_budget()} message cycles remaining out of {self.budget}. "
            "Please prioritize the most important tasks and consider wrapping up soon.",
            "SYSTEM",
        )

    def _manage_budget(self, research_node: ResearchNode) -> bool:
        """Checks budget and handles warnings/exhaustion. Returns True if budget forces a finish."""
        if self.budget is None:
            return False # No budget set, no action needed

        if self.is_budget_exhausted(): # True if message_cycles_used >= self.budget
            # If budget_warning_shown is False, it means this is the first time we've hit self.budget
            # This triggers buffer addition.
            if not self.budget_warning_shown:
                self._handle_initial_budget_depletion(research_node)
                return False # Continue with the buffer, not finishing yet.
            # If budget_warning_shown is True, it means buffer was already added (or warning shown for approaching)
            # and now we've truly used up everything (original budget + buffer).
            else:
                # This check ensures we only prompt for extension if cycles used are AT or EXCEED the (potentially buffered) budget
                if self.message_cycles_used >= self.budget:
                    return self._handle_budget_exhaustion(research_node)

        # Not exhausted yet, but check if approaching limit (and warning not yet shown)
        elif self.is_approaching_budget_limit() and not self.budget_warning_shown:
            self._handle_approaching_budget_warning(research_node)

        return False # No budget-forced finish by default


    def emergency_shutdown(self):
        # This method is called by CommandProcessor now.
        # The primary effect is that the current_engine_state.should_finish will be true.
        # For immediate effect, if execute() is somehow still active, we need a flag.
        # However, CommandProcessor.process will return a state with should_finish=True
        # which should terminate the loop in execute().
        # For an external call to emergency_shutdown, we'd need an instance flag.
        # Let's assume this is primarily for in-cycle shutdowns via command.
        # If a more general emergency stop is needed, an instance variable like self._external_shutdown_requested
        # would be checked at the start of the execute loop.
        # For now, this primarily signals that the *next* check of should_finish in the loop will be true.
        pass


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

    def process_commands(
        self, text: str, current_state_machine_node: "TaskTreeNode", current_engine_state: EngineProcessingState
    ) -> EngineProcessingState:
        """
        Process commands from text using the CommandProcessor.
        Args:
            text: The text containing commands to process.
            current_state_machine_node: The current state machine node.
            current_engine_state: The current engine processing state.
        Returns:
            EngineProcessingState: The new engine state after command processing.
        """
        processor = CommandProcessor(self, self.command_registry, self.command_context_factory)
        # CommandProcessor.process now takes the current state and returns the new state
        return processor.process(text, current_state_machine_node, current_engine_state)

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
            str: The full response string from the LLM.
        Raises:
            KeyboardInterrupt: If the user cancels during retry.
        """
        while True:
            try:
                response_generator = self.llm_interface.send_request(request)
                try:
                    full_llm_response = next(response_generator)
                    research_node.get_logger().log_llm_response(full_llm_response)
                    return full_llm_response
                except StopIteration:
                    # LLM finished generating without error, but response is empty
                    research_node.get_logger().log_llm_response("") # Log empty response
                    return ""
            except KeyboardInterrupt:
                print("\nLLM request interrupted by user during retry prompt. Re-raising.")
                raise # Re-raise to be handled by a higher level if necessary
            except Exception:
                import traceback
                print("\n\n===== LLM INTERFACE ERROR =====")
                print(traceback.format_exc())
                print("===============================")
                print("\nPress Enter to retry or Ctrl+C to exit...")
                try:
                    input()  # Wait for user input; if Ctrl+C here, it's a KeyboardInterrupt
                    print("Retrying LLM request...")
                except KeyboardInterrupt:
                    # This ensures the interrupt during input() is caught and re-raised
                    # to be handled by the outer KeyboardInterrupt handler.
                    raise
                # KeyboardInterrupt is already handled by the outer try/except for this specific case.
                # If input() itself is interrupted, no specific handling needed here other than the loop continuing or KI propagating.

    def _generate_final_report(self) -> str:
        """Generate a summary of all artifacts created during the research. (Currently not called automatically)"""
        # Uses self.final_root_completion_message which is set at the end of execute()
        return self.report_generator.generate_final_report(self.research, self.interface, getattr(self, 'final_root_completion_message', None))
