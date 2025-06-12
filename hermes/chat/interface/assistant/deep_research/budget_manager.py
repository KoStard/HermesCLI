import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode


logger = logging.getLogger(__name__)


class BudgetManager:
    """Manages the message cycle budget for the research process."""

    def __init__(self, initial_budget: int | None = None):
        self.budget: int | None = initial_budget
        self.message_cycles_used: int = 0
        self.cycles_used_since_last_start: int = 0
        self._budget_warning_shown: bool = False
        self._budget_lock = threading.RLock()
        self._budget_exhausted_and_extension_rejected = False

    def set_budget(self, budget_value: int | None):
        """Set the budget for the Deep Research Assistant.
        None means no budget.
        Negative values remove the budget as well.
        """
        if budget_value and budget_value < 0:
            budget_value = None
        self.budget = budget_value
        self._budget_exhausted_and_extension_rejected = False
        self._budget_warning_shown = False  # Reset warning when budget is set/changed
        # Reset cycles used since last start when budget is set/changed
        self.cycles_used_since_last_start = 0

    def get_remaining_budget(self) -> int | None:
        """Get the remaining budget"""
        with self._budget_lock:
            if self.budget is None:
                return None
            return self.budget - self.message_cycles_used

    def is_budget_exhausted(self) -> bool:
        """Check if the budget is exhausted"""
        with self._budget_lock:
            if self.budget is None:
                return False
            return self.message_cycles_used > self.budget

    def increment_cycles_and_manage_budget(self, research_node: "ResearchNode") -> bool:
        """Checks budget and handles warnings/exhaustion.
        Returns True if budget constraints dictate that research should stop.
        """
        with self._budget_lock:
            self.message_cycles_used += 1
            self.cycles_used_since_last_start += 1

            if self.budget is None:
                return False  # No budget set

            if self._budget_exhausted_and_extension_rejected:
                return True

            return self._handle_budget_state(research_node)

    def _handle_budget_state(self, research_node: "ResearchNode") -> bool:
        """Handle the current budget state and return if research should stop."""
        if self.is_budget_exhausted():
            return self._handle_final_budget_exhaustion(research_node)

        return False

    def _handle_final_budget_exhaustion(self, research_node: "ResearchNode") -> bool:
        """Handles logic when budget (including buffer) is fully exhausted. Returns True if research should finish."""
        assert self.budget is not None
        print("\n===== BUDGET COMPLETELY EXHAUSTED =====")
        print(
            f"Current usage: {self.message_cycles_used} cycles (Initial budget: {self.budget})",
        )
        user_input = self._get_confirmation("Would you like to add 20 more cycles to continue? (y/N): ", {"y", "n"})
        if user_input == "y":
            additional_cycles = 20
            self.budget += additional_cycles
            # budget_warning_shown remains true as user opted to extend
            print(f"Added {additional_cycles} more cycles. New budget ceiling: {self.budget}")
            return False
        print("Finishing research due to budget constraints.")
        self._budget_exhausted_and_extension_rejected = True
        return True

    def _get_confirmation(self, message: str, options: set[str]) -> str:
        response = input(message).strip().lower()
        if response not in options:
            print("Please choose one of the options")
            return self._get_confirmation(message, options)
        return response

    def _is_approaching_budget_limit(self) -> bool:
        """Check if we're approaching the budget limit (e.g., within 10 cycles)"""
        with self._budget_lock:
            if self.budget is None:
                return False
            remaining = self.get_remaining_budget()
            # Ensure remaining is not None before comparison
            return remaining is not None and 0 < remaining <= 10
