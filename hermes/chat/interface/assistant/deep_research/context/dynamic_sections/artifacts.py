from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.context.content_truncator import ContentTruncator
from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicSectionData, DynamicSectionRenderer

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode
    from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Primitive Data Structure ---
@dataclass(frozen=True)
class PrimitiveArtifactData:
    """Immutable, primitive representation of an Artifact for comparison."""

    name: str
    content: str
    short_summary: str | None
    is_external: bool
    is_fully_visible: bool  # Added to track visibility state directly
    owner_title: str | None = None  # Added to track ownership for node artifacts
    research_name: str | None = None  # from which research is this node from

    @staticmethod
    def from_artifact(
        artifact: "Artifact",
        owner_title: str | None = None,
        is_fully_visible: bool = False,
        research_name: str | None = None,
    ) -> "PrimitiveArtifactData":
        return PrimitiveArtifactData(
            name=artifact.name,
            content=artifact.content,
            is_external=artifact.is_external,
            short_summary=artifact.short_summary,
            is_fully_visible=is_fully_visible,
            owner_title=owner_title,
            research_name=research_name,
        )


# --- Data ---
@dataclass(frozen=True)
class ArtifactsSectionData(DynamicSectionData):
    # Store primitive representations
    external_files: tuple[PrimitiveArtifactData, ...] = field(default_factory=tuple)
    node_artifacts: tuple[PrimitiveArtifactData, ...] = field(default_factory=tuple)

    @staticmethod
    def from_artifact_lists(
        external_files_dict: dict[str, "Artifact"],
        node_artifacts_list: list[tuple["ResearchNode", "Artifact", bool, str | None]],
    ) -> "ArtifactsSectionData":
        # Convert external files dict to primitive tuple
        external_primitives = tuple(
            PrimitiveArtifactData.from_artifact(artifact, is_fully_visible=True)  # External are always visible
            for name, artifact in sorted(external_files_dict.items())  # Sort for consistent order
        )

        # Convert node artifacts list to primitive tuple
        sorted_node_artifacts = sorted(node_artifacts_list, key=lambda x: (x[0].get_title(), x[1].name))
        node_primitives = tuple(
            PrimitiveArtifactData.from_artifact(artifact, node.get_title(), is_fully_visible, research_name)
            for node, artifact, is_fully_visible, research_name in sorted_node_artifacts
        )

        return ArtifactsSectionData(external_files=external_primitives, node_artifacts=node_primitives)


# --- Renderer ---
class ArtifactsSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/artifacts.mako")

    def render(self, data: ArtifactsSectionData, future_changes: int) -> str:
        if future_changes:
            return """<artifacts>
New artifacts have been added in the future, redacted the old from history to keep it clean.
</artifacts>"""
        # Pass the primitive tuples directly
        context = {
            "external_files_data": data.external_files,  # Tuple[PrimitiveArtifactData]
            "node_artifacts_data": data.node_artifacts,  # Tuple[PrimitiveArtifactData]
            "truncator": ContentTruncator,
        }
        return self._render_template(context)
