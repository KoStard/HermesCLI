import subprocess
from typing import Any, Dict
from .base import Task

class ShellTask(Task):
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
