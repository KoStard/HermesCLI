from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.framework.context.dynamic_sections import DynamicSectionData, DynamicSectionRenderer

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.framework.research import ResearchNode
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Data ---
@dataclass(frozen=True)
class ProblemDefinitionData(DynamicSectionData):
    title: str
    content: str
    depth: int

    @staticmethod
    def from_node(target_node: "ResearchNode") -> "ProblemDefinitionData":
        return ProblemDefinitionData(
            title=target_node.get_title(),
            content=target_node.get_problem().content,
            depth=target_node.get_depth_from_root(),
        )


# --- Renderer ---
class ProblemDefinitionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/problem_definition.mako")

    def render(self, data: ProblemDefinitionData, future_changes: int) -> str:  # type: ignore[override]
        context = {
            "title": data.title,
            "content": data.content,
            "depth": data.depth,
        }
        return self._render_template(context)
