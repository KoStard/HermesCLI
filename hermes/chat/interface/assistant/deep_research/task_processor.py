import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, Generic

from hermes.chat.interface.assistant.deep_research.command_processor import CommandProcessor
from hermes.chat.interface.assistant.deep_research.commands import ResearchCommandContextFactory, ResearchCommandContextType
from hermes.chat.interface.assistant.deep_research.research.research_node_component.problem_definition_manager import (
    ProblemStatus,
)
from hermes.chat.interface.assistant.deep_research.research.research_node_history_adapter import ResearchNodeHistoryAdapter
from hermes.chat.interface.assistant.framework.engine_shutdown_requested_exception import EngineShutdownRequestedError
from hermes.chat.interface.commands.command_parser import CommandParser

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.budget_manager import BudgetManager
    from hermes.chat.interface.assistant.deep_research.context import AssistantInterface
    from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicDataTypeToRendererMap
    from hermes.chat.interface.assistant.deep_research.engine import ResearchEngine
    from hermes.chat.interface.assistant.deep_research.research import Research, ResearchNode
    from hermes.chat.interface.assistant.deep_research.status_printer import StatusPrinter
    from hermes.chat.interface.assistant.framework.llm_interface import LLMInterface
    from hermes.chat.interface.commands.command import CommandRegistry
    from hermes.chat.interface.templates.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class TaskProcessorRunResult(Enum):
    TASK_COMPLETED_OR_PAUSED = auto()  # The task was processed, and is now finished, failed, or pending children
    ENGINE_STOP_REQUESTED = auto()  # The task processing led to a budget exhaustion or shutdown command
    TASK_FAILED = auto()


class TaskProcessorCancelledError(Exception):
    pass


class TaskProcessor(Generic[ResearchCommandContextType]):
    """Manages the execution lifecycle of a single TaskTreeNode.
    It contains the primary loop for interacting with the LLM,
    processing commands, updating task history, and managing the task's state.
    """

    def __init__(
        self,
        research_node: "ResearchNode",
        research_project: "Research",
        llm_interface_to_use: "LLMInterface",
        command_registry_to_use: "CommandRegistry",
        command_context_factory_to_use: "ResearchCommandContextFactory[ResearchCommandContextType]",
        template_manager_to_use: "TemplateManager",
        dynamic_section_renderer_registry: "DynamicDataTypeToRendererMap",
        agent_interface_for_ui: "AssistantInterface",
        status_printer_to_use: "StatusPrinter",
        budget_manager: "BudgetManager",
        command_parser: CommandParser,
        engine: "ResearchEngine",
    ):
        self.current_node = research_node
        self.research_project = research_project
        self.llm_interface = llm_interface_to_use
        self.command_registry = command_registry_to_use
        self.command_context_factory = command_context_factory_to_use
        self.template_manager = template_manager_to_use
        self.renderer_registry = dynamic_section_renderer_registry
        self.agent_interface = agent_interface_for_ui
        self.status_printer = status_printer_to_use
        self.budget_manager = budget_manager
        self.command_parser = command_parser
        self._engine = engine

    def run(self) -> TaskProcessorRunResult:
        """Runs the assigned task_tree_node until its status changes significantly
        (FINISHED, FAILED, PENDING), or budget/shutdown dictates a stop.
        """
        while not self._is_interrupted:
            state = self._execute_task_processing_cycle_and_catch(self.current_node)
            if state:
                return state

        self._handle_interruption()
        return TaskProcessorRunResult.TASK_COMPLETED_OR_PAUSED

    def get_engine(self) -> "ResearchEngine":
        return self._engine

    @property
    def _is_interrupted(self) -> bool:
        return self.current_node.get_problem_status() in {ProblemStatus.CANCELLED} or self._engine.engine_interrupted

    def _handle_interruption(self):
        if self.current_node.get_problem_status() not in {ProblemStatus.CANCELLED, ProblemStatus.FAILED, ProblemStatus.FINISHED}:
            self.current_node.set_problem_status(ProblemStatus.CANCELLED)

    def _execute_task_processing_cycle_and_catch(self, research_node: "ResearchNode") -> TaskProcessorRunResult | None:
        try:
            state = self._execute_task_processing_cycle(self.current_node)
            if state:
                return state
        except EngineShutdownRequestedError:
            return TaskProcessorRunResult.ENGINE_STOP_REQUESTED
        except TaskProcessorCancelledError:
            return TaskProcessorRunResult.TASK_COMPLETED_OR_PAUSED
        except Exception as e:
            error_message = f"Task execution failed for {research_node.get_title()}"
            logger.warning(error_message, e)
            self.current_node.set_problem_status(ProblemStatus.FAILED)
            return TaskProcessorRunResult.TASK_FAILED

    def _execute_task_processing_cycle(self, research_node: "ResearchNode") -> TaskProcessorRunResult | None:
        """Execute a single task processing cycle."""

        # Handle budget updates
        budget_outcome = self._manage_budget_during_cycle(research_node)
        if budget_outcome:
            return budget_outcome

        # Increment iteration counter for auto-close functionality
        research_node.increment_iteration()

        # Get LLM response
        full_llm_response = self._prepare_and_execute_llm_request(research_node)

        # Process commands from response
        self._process_llm_response_commands(full_llm_response)

        # Update history and status
        self._perform_post_cycle_updates(research_node)

        # Check if processing is complete
        return self._determine_task_processor_outcome(research_node)

    def _prepare_and_execute_llm_request(self, research_node: "ResearchNode") -> str:
        """Prepares UI, history, generates and executes LLM request, returns LLM response."""
        self._prepare_interface_and_history_for_node(research_node)
        history_messages = ResearchNodeHistoryAdapter(research_node).get_history_messages(
            self.template_manager,
            self.renderer_registry,
            research_node.get_history().get_initial_interface_content(),
        )

        # Get interface content and generate request
        request = self._generate_llm_request(research_node, history_messages)

        return self._handle_llm_request(request, research_node)

    def _prepare_interface_and_history_for_node(self, research_node: "ResearchNode"):
        """Gathers current interface state and updates history for the given node."""
        static_interface_content, current_dynamic_data = self.agent_interface.render_problem_defined(
            self.research_project,
            research_node,
            self.research_project.get_permanent_logs().get_logs(),
            self.budget_manager.budget,  # Get budget from BudgetManager
            self.budget_manager.get_remaining_budget(),  # Get remaining from BudgetManager
        )
        node_history = research_node.get_history()
        if not node_history.has_initial_interface():
            node_history.set_initial_interface_content(static_interface_content, current_dynamic_data)
        else:
            node_history.update_static_content_in_initial_interface(static_interface_content)

        current_auto_reply_aggregator = node_history.get_auto_reply_aggregator()
        current_auto_reply_aggregator.update_dynamic_sections(current_dynamic_data)
        node_history.prepare_and_add_auto_reply_block()

    def _generate_llm_request(self, research_node: "ResearchNode", history_messages: list[dict]) -> dict:
        """Generate the LLM request with all necessary data."""
        llm_request = self.llm_interface.generate_request(history_messages)

        # Log the request
        research_node.get_logger().log_llm_request(history_messages, llm_request)

        return llm_request

    def _process_llm_response_commands(self, full_llm_response: str):
        """Processes commands from the LLM response and returns the updated processing state."""
        command_processor = CommandProcessor(
            self,  # TaskProcessor instance
            self.command_parser,
            self.command_registry,
            self.command_context_factory,
        )
        command_processor.process(full_llm_response, self.current_node)

    def _manage_budget_during_cycle(self, research_node: "ResearchNode") -> TaskProcessorRunResult | None:
        """Checks budget; if exhausted and stop is dictated, returns ENGINE_STOP_REQUESTED."""
        budget_finish_signal = self.budget_manager.increment_cycles_and_manage_budget(research_node)
        if budget_finish_signal:
            if research_node.get_problem_status() not in [ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.CANCELLED]:
                research_node.set_problem_status(ProblemStatus.FAILED)
            return TaskProcessorRunResult.ENGINE_STOP_REQUESTED
        return None

    def _perform_post_cycle_updates(self, research_node: "ResearchNode"):
        """Saves node history and prints the current status."""
        self.status_printer.print_status(self.research_project)

    def _determine_task_processor_outcome(self, research_node: "ResearchNode") -> TaskProcessorRunResult | None:
        """Determines if the task processing should conclude for this cycle."""
        current_node_status = research_node.get_problem_status()
        is_task_terminal = current_node_status in [ProblemStatus.FINISHED, ProblemStatus.FAILED, ProblemStatus.PENDING]

        if is_task_terminal:
            return TaskProcessorRunResult.TASK_COMPLETED_OR_PAUSED

        return None

    def _handle_llm_request(self, request, research_node: "ResearchNode"):
        """Handle the LLM request with retry capability."""
        while True:
            try:
                full_llm_response = self._attempt_llm_request(request, research_node)
                # On success, commit the turn and return
                research_node.get_history().commit_llm_turn(full_llm_response)
                return full_llm_response
            except KeyboardInterrupt:
                research_node.get_history().rollback_last_auto_reply()
                print("\nLLM request interrupted by user during retry prompt. Re-raising.")
                raise
            except Exception as e:
                research_node.get_history().rollback_last_auto_reply()
                if not self._handle_llm_error(e):
                    raise
                # If retrying, we must re-prepare the auto-reply block for the next attempt
                research_node.get_history().prepare_and_add_auto_reply_block()

    def _attempt_llm_request(self, request, research_node: "ResearchNode") -> str:
        """Try to get a response from the LLM, but do not commit it yet."""
        response_generator = self.llm_interface.send_request(request)

        try:
            full_llm_response_pieces = []
            for piece in response_generator:
                full_llm_response_pieces.append(piece)
                if self._is_interrupted:
                    raise TaskProcessorCancelledError()
            full_llm_response = "".join(full_llm_response_pieces)
            research_node.get_logger().log_llm_response(full_llm_response)
            return full_llm_response
        except StopIteration:
            research_node.get_logger().log_llm_response("")
            return ""

    def _handle_llm_error(self, exception: Exception) -> bool:
        """Handle LLM interface errors with option to retry.

        Returns:
            bool: True if should retry, False otherwise
        """
        if isinstance(exception, TaskProcessorCancelledError):
            return False

        import traceback

        print("\n\n===== LLM INTERFACE ERROR =====")
        print(traceback.format_exc())
        print("===============================")
        print("\nPress Enter to retry or Ctrl+C to exit...")

        try:
            input()
            print("Retrying LLM request...")
            return True
        except KeyboardInterrupt:
            return False

    def add_command_output_to_auto_reply(self, command_name: str, args: dict, output: str, current_node: "ResearchNode"):
        """Add command output to be included in the automatic response for the current node."""
        if not output:  # Ensure output is not None for the dict
            output = ""

        auto_reply_aggregator = current_node.get_history().get_auto_reply_aggregator()
        auto_reply_aggregator.add_command_output(command_name, {"args": args, "output": output})
