from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskProcessingState:
    """Immutable state for command processing cycle within a TaskProcessor."""

    current_task_finished_or_failed: bool = False
    engine_shutdown_requested: bool = False
    commands_executed_this_turn: bool = False
    report_this_turn: str = ""
    execution_status_this_turn: dict[str, Any] = field(default_factory=dict)

    def with_current_task_finished_or_failed(self, finished_or_failed: bool) -> "TaskProcessingState":
        """Create new state with updated task finished status."""
        return self._replace(current_task_finished_or_failed=finished_or_failed)

    def with_engine_shutdown_requested(self, shutdown_requested: bool) -> "TaskProcessingState":
        """Create new state with updated shutdown request status."""
        return self._replace(engine_shutdown_requested=shutdown_requested)

    def with_command_results(
        self, executed: bool, report: str, status: dict[str, Any]
    ) -> "TaskProcessingState":
        """Create new state with updated command execution results."""
        return self._replace(
            commands_executed_this_turn=executed,
            report_this_turn=report,
            execution_status_this_turn=status,
        )

    def _replace(self, **changes: Any) -> "TaskProcessingState":
        """Create new state with specified changes."""
        import dataclasses
        return dataclasses.replace(self, **changes)
