from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .base import DynamicSectionData, DynamicSectionRenderer

if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class BudgetSectionData(DynamicSectionData):
    budget: Optional[int]
    remaining_budget: Optional[int]


# --- Renderer ---
class BudgetSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/budget.mako")

    def render(self, data: BudgetSectionData, future_changes: int) -> str:
        context = {
            "budget": data.budget,
            "remaining_budget": data.remaining_budget,
        }
        return self._render_template(context)
