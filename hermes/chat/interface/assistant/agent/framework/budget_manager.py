from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.agent.framework.research import ResearchNode


class BudgetManager:
    """Manages the message cycle budget for the research process."""

    def __init__(self):
        self.budget: int | None = None  # No budget by default
        self.message_cycles_used: int = 0
        self.budget_warning_shown: bool = False

    def set_budget(self, budget_value: int | None):
        """
        Set the budget for the Deep Research Assistant.
        None means no budget.
        """
        self.budget = budget_value
        self.budget_warning_shown = False  # Reset warning when budget is set/changed
        if budget_value is not None:
            print(f"Budget set to {budget_value} message cycles.")
        else:
            print("Budget has been cleared (unlimited cycles).")

    def increment_message_cycles(self):
        """Increment the message cycles counter"""
        self.message_cycles_used += 1

    def get_remaining_budget(self) -> int | None:
        """Get the remaining budget"""
        if self.budget is None:
            return None
        return self.budget - self.message_cycles_used

    def is_budget_exhausted(self) -> bool:
        """Check if the budget is exhausted"""
        if self.budget is None:
            return False
        return self.message_cycles_used >= self.budget

    def is_approaching_budget_limit(self) -> bool:
        """Check if we're approaching the budget limit (e.g., within 10 cycles)"""
        if self.budget is None:
            return False
        remaining = self.get_remaining_budget()
        # Ensure remaining is not None before comparison
        return remaining is not None and 0 < remaining <= 10

    def manage_budget(self, research_node: "ResearchNode") -> bool:
        """
        Checks budget and handles warnings/exhaustion.
        Returns True if budget constraints dictate that research should stop.
        """
        if self.budget is None:
            return False  # No budget set

        return self._handle_budget_state(research_node)

    def _handle_budget_state(self, research_node: "ResearchNode") -> bool:
        """Handle the current budget state and return if research should stop."""
        if self.is_budget_exhausted():
            return self._handle_budget_exhaustion(research_node)
        elif self.is_approaching_budget_limit() and not self.budget_warning_shown:
            self._handle_approaching_budget_warning(research_node)

        return False

    def _handle_budget_exhaustion(self, research_node: "ResearchNode") -> bool:
        """Handle budget exhaustion cases."""
        if not self.budget_warning_shown:
            # First time hitting budget, add buffer
            self._handle_initial_budget_depletion(research_node)
            return False
        elif self.budget is not None and self.message_cycles_used >= self.budget:
            # Budget truly exhausted after buffer
            return self._handle_final_budget_exhaustion(research_node)

        return False

    def _handle_final_budget_exhaustion(self, research_node: "ResearchNode") -> bool:
        """Handles logic when budget (including buffer) is fully exhausted. Returns True if research should finish."""
        assert self.budget is not None
        print("\n===== BUDGET COMPLETELY EXHAUSTED =====")
        print(
            f"Current usage: {self.message_cycles_used} cycles (Initial budget: {self.budget - 10 if self.budget_warning_shown else self.budget})"
        )
        user_input = input("Would you like to add 20 more cycles to continue? (y/N): ").strip().lower()
        if user_input == "y":
            additional_cycles = 20
            self.budget += additional_cycles
            # budget_warning_shown remains true as user opted to extend
            print(f"Added {additional_cycles} more cycles. New budget ceiling: {self.budget}")
            research_node.get_history().get_auto_reply_aggregator().add_internal_message_from(
                f"The budget has been extended with {additional_cycles} additional cycles. New total: {self.budget} cycles.",
                "SYSTEM",
            )
            return False  # Continue with extended budget
        else:
            print("Finishing research due to budget constraints.")
            research_node.get_history().get_auto_reply_aggregator().add_internal_message_from(
                "Research stopped due to budget exhaustion (user declined extension).", "SYSTEM"
            )
            return True  # Signal to finish

    def _handle_initial_budget_depletion(self, research_node: "ResearchNode") -> None:
        """Handles logic when budget is first hit, adds a buffer."""
        assert self.budget is not None
        self.budget_warning_shown = True  # Mark that the initial depletion and buffer addition has occurred.

        print("\n===== BUDGET ALERT =====")
        print(f"Budget of {self.budget} message cycles has been reached.")

        buffer_cycles = 10
        self.budget += buffer_cycles  # Add buffer to the current budget
        print(f"Adding a one-time buffer of {buffer_cycles} cycles. New budget ceiling: {self.budget}")
        print("The assistant will be notified to wrap up quickly.")
        research_node.get_history().get_auto_reply_aggregator().add_internal_message_from(
            f"⚠️ BUDGET ALERT: The initial message cycle budget has been reached. "
            f"A buffer of {buffer_cycles} additional cycles has been added. New budget ceiling is {self.budget} cycles. "
            "Please finalize your work as quickly as possible.",
            "SYSTEM",
        )

    def _handle_approaching_budget_warning(self, research_node: "ResearchNode") -> None:
        """Handles logic when nearing the budget limit."""
        self.budget_warning_shown = True  # Warning shown, so next exhaustion will be final.
        print("\n===== BUDGET WARNING =====")
        remaining_budget = self.get_remaining_budget()
        print(f"Approaching budget limit. {remaining_budget} cycles remaining out of {self.budget}.")
        research_node.get_history().get_auto_reply_aggregator().add_internal_message_from(
            f"⚠️ BUDGET WARNING: Only {remaining_budget} message cycles remaining out of {self.budget}. "
            "Please prioritize the most important tasks and consider wrapping up soon.",
            "SYSTEM",
        )
