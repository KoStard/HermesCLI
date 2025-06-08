import threading
from pathlib import Path
from typing import Generic

from hermes.chat.interface.assistant.deep_research.budget_manager import BudgetManager
from hermes.chat.interface.assistant.deep_research.commands import ResearchCommandContextFactory, ResearchCommandContextType
from hermes.chat.interface.assistant.deep_research.context import AssistantInterface
from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicDataTypeToRendererMap
from hermes.chat.interface.assistant.deep_research.report import ReportGenerator
from hermes.chat.interface.assistant.deep_research.research import ResearchNode
from hermes.chat.interface.assistant.deep_research.research.file_system.dual_directory_file_system import DualDirectoryFileSystem
from hermes.chat.interface.assistant.deep_research.research.repo import Repo
from hermes.chat.interface.assistant.deep_research.research.research import Research
from hermes.chat.interface.assistant.deep_research.research.research_node import ResearchNodeImpl
from hermes.chat.interface.assistant.deep_research.research.research_node_component.problem_definition_manager import (
    ProblemDefinition,
    ProblemStatus,
)
from hermes.chat.interface.assistant.deep_research.status_printer import StatusPrinter
from hermes.chat.interface.assistant.deep_research.task_processor import TaskProcessor, TaskProcessorRunResult
from hermes.chat.interface.assistant.deep_research.task_tree.task_tree import TaskTreeImpl
from hermes.chat.interface.assistant.framework.llm_interface import (
    LLMInterface,
)
from hermes.chat.interface.commands.command import CommandRegistry
from hermes.chat.interface.commands.command_parser import CommandParser
from hermes.chat.interface.templates.template_manager import TemplateManager


class ResearchEngine(Generic[ResearchCommandContextType]):
    """Core engine for Deep Research functionality, independent of UI implementation"""

    def __init__(
        self,
        root_dir: Path,
        llm_interface: LLMInterface,
        command_registry: CommandRegistry,
        command_context_factory: ResearchCommandContextFactory[ResearchCommandContextType],
        template_manager: TemplateManager,
        renderer_registry: DynamicDataTypeToRendererMap,
        agent_interface: AssistantInterface,
        report_generator: ReportGenerator,
        status_printer: StatusPrinter,
        research_name: str | None,
    ):
        self.command_context_factory = command_context_factory
        self.template_manager = template_manager
        self.renderer_registry = renderer_registry
        self.interface = agent_interface
        self.report_generator = report_generator
        self.status_printer = status_printer
        self.engine_should_stop = False
        self.engine_interrupted = False
        self.dual_directory_file_system = DualDirectoryFileSystem(root_dir)

        # Initialize repo and load all existing research instances
        self.repo = Repo(root_dir, self.dual_directory_file_system)

        # Set current research
        research_name = research_name or "default_research"
        self.current_research_name = research_name
        self.research = self._get_or_create_research(research_name)

        self.command_registry = command_registry

        # Initialize other components
        self.command_parser = CommandParser(self.command_registry)
        self.llm_interface = llm_interface
        self.budget_manager = BudgetManager()

    def has_root_problem_defined(self) -> bool:
        """Check if the research has a root problem defined"""
        return self.research.has_root_problem_defined()

    def define_root_problem(self, instruction: str):
        """
        Handle the initial problem definition phase.
        """
        current_task_tree = self._get_task_tree_for_current_research()

        problem_definition = ProblemDefinition(content=instruction)
        node = ResearchNodeImpl(
            problem=problem_definition,
            title=self.current_research_name,
            path=self.research.get_root_directory(),
            parent=None,
            task_tree=current_task_tree,
            dual_directory_fs=self.dual_directory_file_system,
        )
        self.research.initiate_research(node)
        node.set_problem_status(ProblemStatus.READY_TO_START)

        self.status_printer.print_status(self.research)

    def add_new_instruction(self, instruction: str):
        """Injects a new user instruction into the current node's context."""
        if not self.research.has_root_problem_defined():
            print("Error: Cannot prepare for new instruction without an active node.")
            return

        root_node = self.research.get_root_node()

        self._create_and_add_new_instruction_message(instruction, root_node)

        # Mark the root problem as in progress
        root_node.set_problem_status(ProblemStatus.READY_TO_START)

    def _create_and_add_new_instruction_message(self, instruction: str, root_node: ResearchNode):
        """Formats the instruction and adds it to the root node's history."""
        formatted_instruction = self.template_manager.render_template("context/new_user_instruction.mako", instruction=instruction)
        history = root_node.get_history()
        auto_reply_aggregator = history.get_auto_reply_aggregator()
        auto_reply_aggregator.add_internal_message_from(formatted_instruction, "USER MESSAGE")

    def execute(self) -> str | None:
        """
        Execute the deep research process. Runs until the current task is completed
        (node finished/failed and focus returns to root, or budget exhausted, or shutdown).
        """
        self._validate_execution_prerequisites()
        self._initialize_execution_state()
        threads = self._execute_task_processing_loop()
        self._wait_for_completion(threads)
        return self._generate_final_report()

    def _validate_execution_prerequisites(self) -> None:
        """Validate that execution can proceed"""
        if not self.has_root_problem_defined():
            raise ValueError("Root problem must be defined before execution")

    def _initialize_execution_state(self) -> None:
        """Initialize engine state for execution"""
        self.engine_should_stop = False
        self.engine_interrupted = False

    def _execute_task_processing_loop(self) -> list:
        """Execute the main task processing loop and return threads"""
        threads = []
        current_task_tree = self._get_task_tree_for_current_research()

        try:
            while not self.engine_should_stop and not self.engine_interrupted:
                next_node = current_task_tree.next()
                if not next_node:
                    break
                thread = self._start_node_processing(next_node)
                threads.append(thread)
        except KeyboardInterrupt:
            self.engine_interrupted = True
            
        return threads

    def _start_node_processing(self, node: ResearchNode) -> threading.Thread:
        """Start processing a single node and return the thread"""
        node.set_problem_status(ProblemStatus.IN_PROGRESS)
        self.status_printer.print_status(self.research)
        thread = threading.Thread(target=self._run_node, args=(node,))
        thread.start()
        return thread

    def _wait_for_completion(self, threads: list) -> None:
        """Wait for all processing threads to complete"""
        for thread in threads:
            thread.join()

    def _get_or_create_research(self, name: str) -> Research:
        """Get existing research or create new one."""
        research = self.repo.get_research(name)
        if not research:
            research = self.repo.create_research(name)
        return research

    def _get_task_tree_for_current_research(self) -> TaskTreeImpl:
        """Get task tree for current research."""
        task_tree = self.repo.get_task_tree(self.current_research_name)
        if not task_tree:
            raise ValueError(f"Task tree not found for research '{self.current_research_name}'")
        return task_tree

    def _generate_final_report(self) -> str | None:
        """Generate final report for current research."""
        root_node = self.research.get_root_node()
        final_root_completion_message = root_node.get_resolution_message()
        return self.report_generator.generate_final_report(self.research, self.interface, final_root_completion_message)

    def _run_node(self, research_node: ResearchNode | None):
        if research_node is None:  # All tasks in the tree are done
            self.engine_should_stop = True
            return

        task_processor = TaskProcessor(
            research_node=research_node,
            research_project=self.research,
            llm_interface_to_use=self.llm_interface,
            command_registry_to_use=self.command_registry,
            command_context_factory_to_use=self.command_context_factory,
            template_manager_to_use=self.template_manager,
            dynamic_section_renderer_registry=self.renderer_registry,
            agent_interface_for_ui=self.interface,
            status_printer_to_use=self.status_printer,
            budget_manager=self.budget_manager,  # Pass BudgetManager instance
            command_parser=self.command_parser,
            engine=self,
        )

        run_result = task_processor.run()

        if run_result == TaskProcessorRunResult.ENGINE_STOP_REQUESTED:
            self.engine_should_stop = True  # Budget exhaustion or shutdown command from task

    def set_budget(self, budget_value: int | None):
        """
        Set the budget for the Deep Research Assistant. Delegates to BudgetManager.
        """
        self.budget_manager.set_budget(budget_value)

    def create_new_research(self, name: str) -> Research:
        """
        Create a new research instance under the repo.
        """
        return self.repo.create_research(name)

    def switch_research(self, name: str):
        """
        Switch to a different research instance.

        Args:
            name: Name of the research instance to switch to

        Raises:
            ValueError: If research doesn't exist
        """
        self.current_research_name = name
        self.research = self._get_or_create_research(name)

    def list_research_instances(self) -> list[str]:
        """
        List all available research instances.

        Returns:
            List of research instance names
        """
        return self.repo.list_research_instances()
