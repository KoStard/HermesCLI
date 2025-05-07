from dataclasses import dataclass
from typing import TYPE_CHECKING

from . import DynamicSectionData, DynamicSectionRenderer

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.files.file_system import (
        Node,
    )
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
    def from_node(target_node: "Node") -> "CriteriaSectionData":
        return CriteriaSectionData(
            criteria=tuple(target_node.criteria),
            criteria_done=tuple(target_node.criteria_done),
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
