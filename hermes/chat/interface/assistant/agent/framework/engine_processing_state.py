from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EngineProcessingState:
    """
    Immutable state representing the outcome of one command processing cycle
    and ongoing engine control flags.
    """

    should_finish: bool = False
    root_completion_message: str | None = None
    commands_executed_this_turn: bool = False
    report_this_turn: str = ""
    execution_status_this_turn: dict[str, Any] = field(default_factory=dict)

    # Helper methods for immutable updates
    def with_should_finish(self, should_finish: bool) -> "EngineProcessingState":
        return self._replace(should_finish=should_finish)

    def with_root_completion_message(self, message: str | None) -> "EngineProcessingState":
        return self._replace(root_completion_message=message)

    def with_command_results(
        self, executed: bool, report: str, status: dict[str, Any]
    ) -> "EngineProcessingState":
        return self._replace(
            commands_executed_this_turn=executed,
            report_this_turn=report,
            execution_status_this_turn=status,
        )

    def _replace(self, **changes: Any) -> "EngineProcessingState":
        # Utility to use dataclasses.replace, helps with type hinting if needed later
        # and provides a single point for potential custom logic if requirements change.
        import dataclasses
        return dataclasses.replace(self, **changes)
