import subprocess
from typing import Any, Dict, Callable
from .base import Task

class ShellTask(Task):
    def __init__(self, task_id: str, task_config: Dict[str, Any], printer: Callable[[str], None]):
        super().__init__(task_id, task_config, printer)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        command = self.get_config('command')
        if not command:
            raise ValueError(f"No command specified for shell task {self.task_id}")

        # Format the command with the current context
        formatted_command = command.format(**context)

        # Execute the shell command
        try:
            result = subprocess.run(formatted_command, shell=True, check=True, capture_output=True, text=True)
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.CalledProcessError as e:
            return {
                'stdout': e.stdout,
                'stderr': e.stderr,
                'returncode': e.returncode,
                'error': str(e)
            }
