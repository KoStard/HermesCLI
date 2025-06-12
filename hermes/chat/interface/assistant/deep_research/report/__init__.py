from abc import ABC, abstractmethod

from hermes.chat.interface.assistant.deep_research.context import AssistantInterface
from hermes.chat.interface.assistant.deep_research.research import Research


class BudgetInfo:
    """Budget information container class for reporting"""

    def __init__(self, budget: int | None = None, used: int = 0, remaining: int | None = None, since_last_start: int = 0):
        self.budget = budget
        self.used = used
        self.remaining = remaining
        self.since_last_start = since_last_start

    def to_dict(self) -> dict[str, int | None]:
        """Convert to dictionary for template rendering"""
        return {"budget": self.budget, "used": self.used, "remaining": self.remaining, "since_last_start": self.since_last_start}


class ReportGenerator(ABC):
    @abstractmethod
    def generate_final_report(
        self,
        research: Research,
        interface: AssistantInterface,
        root_completion_message: str | None = None,
        budget_info: BudgetInfo | None = None,
    ) -> str:
        pass
