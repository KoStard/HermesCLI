from pathlib import Path
from typing import Generic

from hermes.chat.interface.assistant.agent.framework.budget_manager import BudgetManager
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
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemStatus,
)
from hermes.chat.interface.assistant.agent.framework.status_printer import StatusPrinter
from hermes.chat.interface.assistant.agent.framework.task_processor import TaskProcessor, TaskProcessorRunResult
from hermes.chat.interface.assistant.agent.framework.task_tree.task_tree import TaskTreeImpl
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
        self.budget_manager = BudgetManager()

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
        problem_definition = ProblemDefinition(content=instruction)
        node = ResearchNodeImpl(problem=problem_definition, title=instruction, path=self.research.get_root_directory(), parent=None)
        self.research.initiate_research(node)
        self.task_tree.set_root_research_node(self.research.get_root_node())

        self._print_current_status(self.research.get_root_node())

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

    def _create_and_add_new_instruction_message(self, instruction: str, root_node: ResearchNode):
        """Formats the instruction and adds it to the root node's history."""
        formatted_instruction = self.template_manager.render_template(
            "context/new_user_instruction.mako", instruction=instruction
        )
        history = root_node.get_history()
        auto_reply_aggregator = history.get_auto_reply_aggregator()
        auto_reply_aggregator.add_internal_message_from(formatted_instruction, "USER MESSAGE")

    def execute(self) -> str | None:
        """
        Execute the deep research process. Runs until the current task is completed
        (node finished/failed and focus returns to root, or budget exhausted, or shutdown).
        """
        if not self.is_research_initiated():
            raise ValueError("Root problem must be defined before execution")

        engine_should_stop = False
        while not engine_should_stop:
            current_task_tree_node = self.task_tree.next()

            if current_task_tree_node is None: # All tasks in the tree are done
                engine_should_stop = True
                break

            task_processor = TaskProcessor(
                task_tree_node_to_process=current_task_tree_node,
                research_project=self.research,
                llm_interface_to_use=self.llm_interface,
                command_registry_to_use=self.command_registry,
                command_context_factory_to_use=self.command_context_factory,
                template_manager_to_use=self.template_manager,
                dynamic_section_renderer_registry=self.renderer_registry,
                agent_interface_for_ui=self.interface,
                status_printer_to_use=self.status_printer,
                budget_manager=self.budget_manager, # Pass BudgetManager instance
                command_parser=self.command_parser
            )

            run_result = task_processor.run()

            if run_result == TaskProcessorRunResult.ENGINE_STOP_REQUESTED:
                engine_should_stop = True # Budget exhaustion or shutdown command from task

        # After loop execution (all tasks done or engine stopped)
        root_node = self.research.get_root_node()
        final_root_completion_message = root_node.get_resolution_message()

        print("Engine execution cycle complete.")

        return self.report_generator.generate_final_report(
            self.research, self.interface, final_root_completion_message
        )

    def _print_current_status(self, current_node: 'ResearchNode'):
        """
        Print the current status of the research to STDOUT

        Args:
            current_node: The current research node.
        """
        self.status_printer.print_status(current_node, self.research)

    def set_budget(self, budget_value: int | None):
        """
        Set the budget for the Deep Research Assistant. Delegates to BudgetManager.
        """
        self.budget_manager.set_budget(budget_value)
