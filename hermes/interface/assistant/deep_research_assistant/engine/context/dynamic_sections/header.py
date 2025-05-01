from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import DynamicSectionData, DynamicSectionRenderer

if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class HeaderSectionData(DynamicSectionData):
    # Header is static text defined in its template, no data needed from context
    pass


# --- Renderer ---
class HeaderSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/header.mako")

    def render(self, data: HeaderSectionData, future_changes: int) -> str:
        # Header is static, doesn't change based on data or future changes
        return self._render_template({})
