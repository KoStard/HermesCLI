import yaml
import os
from typing import Dict, Any, Callable

from hermes.chat_models.base import ChatModel
from hermes.model_factory import create_model_and_processors
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder
from .tasks.base import Task
from .tasks.llm_task import LLMTask
from .tasks.shell_task import ShellTask
from .tasks.markdown_extraction_task import MarkdownExtractionTask
from .tasks.map_task import MapTask
from .tasks.if_else_task import IfElseTask
from .tasks.sequential_task import SequentialTask
from .tasks.context_extension_task import ContextExtensionTask
from .tasks.chat_application_task import ChatApplicationTask
from hermes.chat_application import ChatApplication
from hermes.ui.chat_ui import ChatUI
from hermes.file_processors.default import DefaultFileProcessor

class WorkflowParser:
    def __init__(self, model: ChatModel, model_id: str, printer: Callable[[str], None]):
        self.model = model
        self.model_id = model_id
        self.printer = printer
        self.chat_application = None

    def parse(self, workflow_file: str) -> Task:
        """
        Parse a YAML workflow file and return the root task.

        Args:
            workflow_file (str): Path to the YAML workflow file.

        Returns:
            Task: The root task of the workflow.

        Raises:
            FileNotFoundError: If the workflow file doesn't exist.
            yaml.YAMLError: If there's an error parsing the YAML file.
            ValueError: If the workflow structure is invalid.
        """
        workflow_dir = os.path.dirname(os.path.abspath(workflow_file))

        try:
            with open(workflow_file, 'r') as file:
                workflow = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing workflow YAML: {e}")

        if not self.validate_workflow(workflow):
            raise ValueError("Invalid workflow structure")
        
        root_id, root_config = next(iter(workflow.items()))
        root_task = self.parse_task(root_id, root_config, workflow_dir)
        return root_task

    def validate_workflow(self, workflow: Dict[str, Any]) -> bool:
        """
        Validate the structure of a parsed workflow.

        Args:
            workflow (Dict[str, Any]): Parsed workflow dictionary.

        Returns:
            bool: True if the workflow is valid, False otherwise.
        """
        if not isinstance(workflow, dict) or len(workflow) != 1:
            return False
        root_id, root_config = next(iter(workflow.items()))
        return isinstance(root_config, dict) and 'type' in root_config

    def parse_task(self, task_id: str, task_config: Dict[str, Any], workflow_dir: str) -> Task:
        """
        Parse a single task configuration and return the appropriate Task object.

        Args:
            task_id (str): The ID of the task.
            task_config (Dict[str, Any]): The configuration for the task.

        Returns:
            Task: An instance of the appropriate Task subclass.

        Raises:
            ValueError: If an unknown task type is encountered.
        """
        task_type = task_config.get('type')
        if task_type == 'llm':
            return LLMTask(task_id, task_config, self.model, self.printer)
        elif task_type == 'shell':
            return ShellTask(task_id, task_config, self.printer)
        elif task_type == 'markdown_extract':
            return MarkdownExtractionTask(task_id, task_config, self.printer)
        elif task_type == 'map':
            sub_task = self.parse_task(f"{task_id}_sub", task_config['task'], workflow_dir)
            return MapTask(task_id, task_config, sub_task, self.printer)
        elif task_type == 'if_else':
            if_task = self.parse_task(f"{task_id}.if", task_config['if_task'], workflow_dir)
            else_task = None
            if 'else_task' in task_config:
                else_task = self.parse_task(f"{task_id}.else", task_config['else_task'], workflow_dir)
            return IfElseTask(task_id, task_config, if_task, self.printer, else_task)
        elif task_type == 'sequential':
            sub_tasks = [self.parse_task(f"{task_id}.{subtask_id}", sub_task, workflow_dir) for subtask_id, sub_task in task_config['tasks'].items()]
            return SequentialTask(task_id, task_config, sub_tasks, self.printer)
        elif task_type == 'context_extension':
            return ContextExtensionTask(task_id, task_config, self.printer, workflow_dir)
        elif task_type == 'chat_application':
            return self.parse_chat_application_task(task_id, task_config)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def parse_chat_application_task(self, task_id: str, task_config: Dict[str, Any]) -> ChatApplicationTask:
        """
        Parse and create a ChatApplicationTask.

        Args:
            task_id (str): The ID of the task.
            task_config (Dict[str, Any]): The configuration for the task.

        Returns:
            ChatApplicationTask: An instance of the ChatApplicationTask.
        """
        if self.chat_application is None:
            ui = ChatUI(prints_raw=True)
            model, model_id, prompt_builder = create_model_and_processors(self.model_id)
            context_orchestrator = ContextOrchestrator([])
            special_command_prompts = {}
            self.chat_application = ChatApplication(model, ui, prompt_builder, special_command_prompts, context_orchestrator)

        return ChatApplicationTask(task_id, task_config, self.chat_application, self.printer)
