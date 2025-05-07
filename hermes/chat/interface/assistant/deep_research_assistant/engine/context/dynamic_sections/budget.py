from dataclasses import dataclass
from typing import TYPE_CHECKING

from . import DynamicSectionData, DynamicSectionRenderer

if TYPE_CHECKING:
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class BudgetSectionData(DynamicSectionData):
    budget: int | None
    remaining_budget: int | None


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
