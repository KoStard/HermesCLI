from dataclasses import dataclass
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.context.dynamic_sections import DynamicSectionData, DynamicSectionRenderer

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research.research_project_component.knowledge_base import (
        KnowledgeBase,
        KnowledgeEntry,
    )
    from hermes.chat.interface.templates.template_manager import (
        TemplateManager,
    )


# --- Primitive Data Structure ---
@dataclass(frozen=True)
class PrimitiveKnowledgeEntryData:
    """Immutable, primitive representation of a KnowledgeEntry."""

    content: str
    author_node_title: str
    timestamp: str
    title: str | None
    tags: tuple[str, ...]  # Use tuple for immutability

    @staticmethod
    def from_entry(entry: "KnowledgeEntry") -> "PrimitiveKnowledgeEntryData":
        return PrimitiveKnowledgeEntryData(
            content=entry.content,
            author_node_title=entry.author_node_title,
            timestamp=entry.timestamp.isoformat(),
            title=entry.title,
            tags=tuple(entry.tags),  # Convert list to tuple
        )


# --- Data ---
@dataclass(frozen=True)
class KnowledgeBaseData(DynamicSectionData):
    # Store primitive representations of knowledge entries
    knowledge_entries: tuple[PrimitiveKnowledgeEntryData, ...]

    @staticmethod
    def from_knowledge_base(
        knowledge_base: "KnowledgeBase",
    ) -> "KnowledgeBaseData":
        entry_data = tuple(
            PrimitiveKnowledgeEntryData.from_entry(entry)
            # Sort by timestamp descending for consistent order (newest first)
            for entry in sorted(knowledge_base.get_entries(), key=lambda x: x.timestamp, reverse=True)
        )
        return KnowledgeBaseData(knowledge_entries=entry_data)


# --- Renderer ---
class KnowledgeBaseRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/knowledge_base.mako")

    def render(self, data: KnowledgeBaseData, future_changes: int) -> str:
        # --- Apply future_changes logic ---
        if future_changes > 0:
            # If the knowledge base changes later, don't show the old version.
            # Return a note or an empty string.
            return "<knowledge_base>\n[Knowledge Base content omitted as it was updated later in the conversation.]\n</knowledge_base>"
            # Alternatively, return "" if we want it completely hidden.

        # Pass the primitive tuple of knowledge entry data
        context = {"knowledge_entries_data": data.knowledge_entries}  # Tuple[PrimitiveKnowledgeEntryData]
        return self._render_template(context)
