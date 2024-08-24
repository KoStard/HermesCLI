from abc import ABC, abstractmethod
from typing import Any, Dict, Callable

from hermes.workflows.context import WorkflowContext

class Task(ABC):
    def __init__(self, task_id: str, task_config: Dict[str, Any], printer: Callable[[str], None]):
        self.task_id = task_id
        self.task_config = task_config
        self.printer = printer
        self.print_output = task_config.get('print_output', False)

    @abstractmethod
    def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        """
        Execute the task and return the result.

        Args:
            context (WorkflowContext): The workflow context.

        Returns:
            Dict[str, Any]: The result of the task execution.
        """
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value for the task.

        Args:
            key (str): The configuration key.
            default (Any, optional): The default value if the key is not found.

        Returns:
            Any: The configuration value.
        """
        return self.task_config.get(key, default)
