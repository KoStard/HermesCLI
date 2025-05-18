from collections import defaultdict
from enum import Enum, auto
from typing import TYPE_CHECKING, Generic

from hermes.chat.interface.assistant.agent.framework.command_processor import CommandProcessor
from hermes.chat.interface.assistant.agent.framework.commands.command_context_factory import CommandContextFactory, CommandContextType
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.history.history_blocks import (
    AutoReply,
    ChatMessage,
)
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.task_processing_state import TaskProcessingState
from hermes.chat.interface.commands.command_parser import CommandParser

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.budget_manager import BudgetManager
    from hermes.chat.interface.assistant.agent.framework.context import AgentInterface
    from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicDataTypeToRendererMap
    from hermes.chat.interface.assistant.agent.framework.llm_interface import LLMInterface
    from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
    from hermes.chat.interface.assistant.agent.framework.status_printer import StatusPrinter
    from hermes.chat.interface.assistant.agent.framework.task_tree import TaskTreeNode
    from hermes.chat.interface.commands.command import CommandRegistry
    from hermes.chat.interface.templates.template_manager import TemplateManager


class TaskProcessorRunResult(Enum):
    TASK_COMPLETED_OR_PAUSED = auto()  # The task was processed, and is now finished, failed, or pending children
    ENGINE_STOP_REQUESTED = auto()     # The task processing led to a budget exhaustion or shutdown command


class TaskProcessor(Generic[CommandContextType]):
    """
    Manages the execution lifecycle of a single TaskTreeNode.
    It contains the primary loop for interacting with the LLM,
    processing commands, updating task history, and managing the task's state.
    """

    def __init__(
        self,
        task_tree_node_to_process: "TaskTreeNode",
        research_project: "Research",
        llm_interface_to_use: "LLMInterface",
        command_registry_to_use: "CommandRegistry",
        command_context_factory_to_use: "CommandContextFactory[CommandContextType]",
        template_manager_to_use: "TemplateManager",
        dynamic_section_renderer_registry: "DynamicDataTypeToRendererMap",
        agent_interface_for_ui: "AgentInterface",
        status_printer_to_use: "StatusPrinter",
        budget_manager: "BudgetManager", # Changed from agent_engine_for_budget
        command_parser: CommandParser,
    ):
        self.task_tree_node_to_process = task_tree_node_to_process
        self.research_project = research_project
        self.llm_interface = llm_interface_to_use
        self.command_registry = command_registry_to_use
        self.command_context_factory = command_context_factory_to_use
        self.template_manager = template_manager_to_use
        self.renderer_registry = dynamic_section_renderer_registry
        self.agent_interface = agent_interface_for_ui
        self.status_printer = status_printer_to_use
        self.budget_manager = budget_manager # Changed attribute name
        self.command_parser = command_parser

    def _prepare_and_execute_llm_request(self, research_node: "ResearchNode") -> str:
        """Prepares UI, history, generates and executes LLM request, returns LLM response."""
        self._prepare_interface_and_history_for_node(research_node)
        history_messages = self._compile_history_for_llm(research_node)

        initial_interface_content = research_node.get_history().get_initial_interface_content()
        if not initial_interface_content:
            # This check is important as _prepare_interface_and_history_for_node should set it.
            raise Exception("Initial interface content not set after preparation phase.")

        llm_request = self.llm_interface.generate_request(
            initial_interface_content, history_messages, research_node.get_path()
        )
        research_node.get_logger().log_llm_request(history_messages, llm_request, initial_interface_content)

        return self._handle_llm_request(llm_request, research_node)

    def _process_llm_response_commands(
        self, full_llm_response: str, current_task_processing_state: TaskProcessingState
    ) -> TaskProcessingState:
        """Processes commands from the LLM response and returns the updated processing state."""
        command_processor = CommandProcessor(
            self, # TaskProcessor instance
            self.command_parser,
            self.command_registry,
            self.command_context_factory
        )
        return command_processor.process(
            full_llm_response, self.task_tree_node_to_process, current_task_processing_state
        )

    def _manage_budget_after_cycle(self, research_node: "ResearchNode") -> TaskProcessorRunResult | None:
        """Checks budget; if exhausted and stop is dictated, returns ENGINE_STOP_REQUESTED."""
        self.budget_manager.increment_message_cycles()
        budget_finish_signal = self.budget_manager.manage_budget(research_node)
        if budget_finish_signal:
            if research_node.get_problem_status() not in [ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED]:
                research_node.set_problem_status(ProblemStatus.FAILED)
            return TaskProcessorRunResult.ENGINE_STOP_REQUESTED
        return None

    def _perform_post_cycle_updates(self, research_node: "ResearchNode"):
        """Saves node history and prints the current status."""
        research_node.get_history().save()
        self.status_printer.print_status(research_node, self.research_project)

    def _determine_task_processor_outcome(
        self, research_node: "ResearchNode", current_task_processing_state: TaskProcessingState
    ) -> TaskProcessorRunResult | None:
        """Determines if the task processing should conclude for this cycle."""
        current_node_status = research_node.get_problem_status()
        is_task_terminal = current_node_status in [ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.PENDING]

        if is_task_terminal or current_task_processing_state.current_task_finished_or_failed:
            if current_task_processing_state.engine_shutdown_requested:
                return TaskProcessorRunResult.ENGINE_STOP_REQUESTED
            return TaskProcessorRunResult.TASK_COMPLETED_OR_PAUSED

        if current_task_processing_state.engine_shutdown_requested:
            return TaskProcessorRunResult.ENGINE_STOP_REQUESTED
        return None

    def run(self) -> TaskProcessorRunResult:
        """
        Runs the assigned task_tree_node until its status changes significantly
        (FINISHED, FAILED, PENDING), or budget/shutdown dictates a stop.
        """
        research_node = self.task_tree_node_to_process.get_research_node()

        while True:
            current_task_processing_state = TaskProcessingState()
            full_llm_response = self._prepare_and_execute_llm_request(research_node)

            current_task_processing_state = self._process_llm_response_commands(
                full_llm_response, current_task_processing_state
            )

            budget_outcome = self._manage_budget_after_cycle(research_node)
            if budget_outcome:
                return budget_outcome # Engine stop requested due to budget

            self._perform_post_cycle_updates(research_node)

            processor_outcome = self._determine_task_processor_outcome(
                research_node, current_task_processing_state
            )
            if processor_outcome:
                return processor_outcome # Task completed/paused or engine shutdown requested

    def _prepare_interface_and_history_for_node(self, research_node: "ResearchNode"):
        """Gathers current interface state and updates history for the given node."""
        static_interface_content, current_dynamic_data = self.agent_interface.render_problem_defined(
            self.research_project,
            research_node,
            self.research_project.get_permanent_logs().get_logs(),
            self.budget_manager.budget, # Get budget from BudgetManager
            self.budget_manager.get_remaining_budget(), # Get remaining from BudgetManager
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

    def _compile_history_for_llm(self, research_node: "ResearchNode") -> list[dict]:
        """Compiles and renders historical messages for LLM input."""
        history_messages = []
        compiled_blocks = research_node.get_history().get_compiled_blocks()
        auto_reply_counter = 0
        iterative_auto_reply_max_length = 5000 # TODO: Make configurable

        for i in range(len(compiled_blocks) - 1, -1, -1):
            block = compiled_blocks[i]
            if isinstance(block, ChatMessage):
                history_messages.append({"author": block.author, "content": block.content})
            elif isinstance(block, AutoReply):
                auto_reply_counter += 1
                current_max_len_for_this_block = None
                if auto_reply_counter > 3:
                    current_max_len_for_this_block = iterative_auto_reply_max_length
                    iterative_auto_reply_max_length = max(iterative_auto_reply_max_length // 2, 300)

                auto_reply_content = self._render_auto_reply_block_for_llm(
                    block,
                    compiled_blocks,
                    i,
                    auto_reply_counter,
                    current_max_len_for_this_block,
                )
                history_messages.append({"author": "user", "content": auto_reply_content})
        return history_messages[::-1]

    def _render_auto_reply_block_for_llm(
        self,
        block: AutoReply,
        compiled_blocks: list,
        current_block_index: int,
        auto_reply_counter: int,
        auto_reply_max_length: int | None,
    ) -> str:
        """Renders a single AutoReply block for LLM history."""
        future_changes_map: dict[int, int] = defaultdict(int)
        for future_block in compiled_blocks[current_block_index + 1:]:
            if isinstance(future_block, AutoReply):
                for section_index, _ in future_block.dynamic_sections:
                    future_changes_map[section_index] += 1

        return block.generate_auto_reply(
            template_manager=self.template_manager,
            renderer_registry=self.renderer_registry,
            future_changes_map=future_changes_map,
            per_command_output_maximum_length=auto_reply_max_length,
        )

    def _handle_llm_request(self, request, research_node: "ResearchNode"):
        """
        Handle the LLM request with retry capability.
        Args:
            request: Request object to send to LLM
            research_node: The current research node for logging
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
                    research_node.get_logger().log_llm_response("")
                    return ""
            except KeyboardInterrupt:
                print("\nLLM request interrupted by user during retry prompt. Re-raising.")
                raise
            except Exception:
                import traceback
                print("\n\n===== LLM INTERFACE ERROR =====")
                print(traceback.format_exc())
                print("===============================")
                print("\nPress Enter to retry or Ctrl+C to exit...")
                try:
                    input()
                    print("Retrying LLM request...")
                except KeyboardInterrupt:
                    raise

    def add_command_output_to_auto_reply(
        self, command_name: str, args: dict, output: str, current_task_tree_node: "TaskTreeNode"):
        """
        Add command output to be included in the automatic response for the current node.
        """
        if not output: # Ensure output is not None for the dict
            output = ""

        auto_reply_aggregator = current_task_tree_node.get_research_node().get_history().get_auto_reply_aggregator()
        auto_reply_aggregator.add_command_output(command_name, {"args": args, "output": output})
