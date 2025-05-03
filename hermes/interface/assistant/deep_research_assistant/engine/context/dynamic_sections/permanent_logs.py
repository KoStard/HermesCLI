from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import DynamicSectionData, DynamicSectionRenderer

if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class PermanentLogsData(DynamicSectionData):
    permanent_logs: list[str]


# --- Renderer ---
class PermanentLogsRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/permanent_logs.mako")

    def render(self, data: PermanentLogsData, future_changes: int) -> str:
        context = {"permanent_logs": data.permanent_logs}
        return self._render_template(context)
