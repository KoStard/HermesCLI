from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicSectionData, \
    DynamicSectionRenderer

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class CriteriaSectionData(DynamicSectionData):
    # These are already primitive, just add factory
    criteria: tuple[str, ...]
    criteria_done: tuple[bool, ...]

    @staticmethod
    def from_node(target_node: "ResearchNode") -> "CriteriaSectionData":
        return CriteriaSectionData(
            criteria=tuple(e.content for e in target_node.get_criteria()),
            criteria_done=tuple(e.is_completed for e in target_node.get_criteria()),
        )


# --- Renderer ---
class CriteriaSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/criteria.mako")

    def render(self, data: CriteriaSectionData, future_changes: int) -> str:
        # Pass the primitive tuples
        context = {
            "criteria_list": data.criteria,  # Tuple[str]
            "criteria_done_list": data.criteria_done,  # Tuple[bool]
        }
        return self._render_template(context)
