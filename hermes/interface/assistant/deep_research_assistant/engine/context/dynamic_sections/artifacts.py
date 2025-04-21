from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING

from .base import DynamicSectionData, DynamicSectionRenderer

# Use TYPE_CHECKING to avoid circular imports at runtime for type hints
if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.files.file_system import Artifact
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager


# --- Primitive Data Structure ---
@dataclass(frozen=True)
class PrimitiveArtifactData:
    """Immutable, primitive representation of an Artifact for comparison."""
    name: str
    content: str
    is_external: bool
    is_fully_visible: bool # Added to track visibility state directly
    owner_title: Optional[str] = None # Added to track ownership for node artifacts

    @staticmethod
    def from_artifact(artifact: "Artifact", owner_title: Optional[str] = None, is_fully_visible: bool = True) -> "PrimitiveArtifactData":
        return PrimitiveArtifactData(
            name=artifact.name,
            content=artifact.content,
            is_external=artifact.is_external,
            is_fully_visible=is_fully_visible,
            owner_title=owner_title
        )


# --- Data ---
@dataclass(frozen=True)
class ArtifactsSectionData(DynamicSectionData):
    # Store primitive representations
    external_files: Tuple[PrimitiveArtifactData, ...] = field(default_factory=tuple)
    node_artifacts: Tuple[PrimitiveArtifactData, ...] = field(default_factory=tuple)

    @staticmethod
    def from_artifact_lists(
        external_files_dict: Dict[str, "Artifact"],
        node_artifacts_list: List[Tuple[str, str, str, bool]] # (owner_title, name, content, is_fully_visible)
    ) -> "ArtifactsSectionData":
        # Convert external files dict to primitive tuple
        external_primitives = tuple(
            PrimitiveArtifactData.from_artifact(artifact, is_fully_visible=True) # External are always visible
            for name, artifact in sorted(external_files_dict.items()) # Sort for consistent order
        )

        # Convert node artifacts list to primitive tuple
        node_primitives = tuple(
            PrimitiveArtifactData(
                name=name,
                content=content,
                is_external=False, # Node artifacts are not external
                is_fully_visible=is_fully_visible,
                owner_title=owner_title
            )
            for owner_title, name, content, is_fully_visible in sorted(node_artifacts_list, key=lambda x: (x[0], x[1])) # Sort
        )

        return ArtifactsSectionData(
            external_files=external_primitives,
            node_artifacts=node_primitives
        )


# --- Renderer ---
class ArtifactsSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/artifacts.mako")

    def render(self, data: ArtifactsSectionData, future_changes: int) -> str:
        # Import ContentTruncator locally to avoid potential module-level issues
        # and keep it close to where it's used.
        from hermes.interface.assistant.deep_research_assistant.engine.context.content_truncator import ContentTruncator
        # Pass the primitive tuples directly
        context = {
            "external_files_data": data.external_files, # Tuple[PrimitiveArtifactData]
            "node_artifacts_data": data.node_artifacts, # Tuple[PrimitiveArtifactData]
            "truncator": ContentTruncator, # Pass the class
        }
        return self._render_template(context)
