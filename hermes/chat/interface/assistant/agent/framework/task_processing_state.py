from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskProcessingState:
    """Immutable state for command processing cycle within a TaskProcessor."""

    current_task_finished_or_failed: bool = False
    engine_shutdown_requested: bool = False
    report_this_turn: str = ""

    def with_current_task_finished_or_failed(self, finished_or_failed: bool) -> "TaskProcessingState":
        """Create new state with updated task finished status."""
        return self._replace(current_task_finished_or_failed=finished_or_failed)

    def with_engine_shutdown_requested(self, shutdown_requested: bool) -> "TaskProcessingState":
        """Create new state with updated shutdown request status."""
        return self._replace(engine_shutdown_requested=shutdown_requested)

    def _replace(self, **changes: Any) -> "TaskProcessingState":
        """Create new state with specified changes."""
        import dataclasses

        return dataclasses.replace(self, **changes)
