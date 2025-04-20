import traceback
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager
    # Import primitive data types as well if needed for type hints
    from .data import (
        DynamicSectionData, HeaderSectionData, PermanentLogsData, BudgetSectionData,
        ArtifactsSectionData, ProblemHierarchyData, CriteriaSectionData, SubproblemsSectionData,
        ProblemPathHierarchyData, KnowledgeBaseData, GoalSectionData,
        PrimitiveArtifactData, PrimitiveSubproblemData, PrimitiveNodePathData, PrimitiveKnowledgeEntryData
    )
    from hermes.interface.assistant.deep_research_assistant.engine.context.content_truncator import ContentTruncator


# --- Base Renderer ---

class DynamicSectionRenderer(ABC):
    """Base class for rendering dynamic sections."""
    def __init__(self, template_manager: "TemplateManager", template_name: str):
        self.template_manager = template_manager
        self.template_name = template_name

    @abstractmethod
    def render(self, data: "DynamicSectionData", future_changes: int) -> str:
        """
        Renders the section based on the provided data and future changes.

        Args:
            data: The specific data dataclass instance for this section.
            future_changes: The number of times this section changes *after*
                            the current instance in the history.

        Returns:
            The rendered HTML/Markdown string for the section, or an error message.
        """
        pass

    def _render_template(self, context: dict) -> str:
        """Helper to render the template with common error handling."""
        try:
            return self.template_manager.render_template(self.template_name, **context)
        except Exception as e:
            print(f"\n--- ERROR RENDERING TEMPLATE: {self.template_name} ---")
            traceback.print_exc()
            print("--- END ERROR ---")
            # Corrected f-string for artifact name
            artifact_name = f"render_error_{self.template_name.replace('/', '_').replace('.mako', '')}"
            error_message = (
                f"**SYSTEM ERROR:** Failed to render the '{self.template_name}' section. "
                f"Please create an artifact named '{artifact_name}' "
                f"with the following content:\n```\n{traceback.format_exc()}\n```\n"
                "Then, inform the administrator."
            )
            # We might want to wrap this in XML tags appropriate for the interface
            # For now, return the raw error message for inclusion.
            return f"<error context=\"Rendering {self.template_name}\">\n{error_message}\n</error>"


# --- Concrete Renderers ---

class HeaderSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/header.mako")

    def render(self, data: "HeaderSectionData", future_changes: int) -> str:
        # Header is static, doesn't change based on data or future changes
        return self._render_template({})


class PermanentLogsRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/permanent_logs.mako")

    def render(self, data: "PermanentLogsData", future_changes: int) -> str:
        context = {"permanent_logs": data.permanent_logs}
        return self._render_template(context)


class BudgetSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/budget.mako")

    def render(self, data: "BudgetSectionData", future_changes: int) -> str:
        context = {
            "budget": data.budget,
            "remaining_budget": data.remaining_budget,
        }
        return self._render_template(context)


class ArtifactsSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/artifacts.mako")

    def render(self, data: "ArtifactsSectionData", future_changes: int) -> str:
        # Import ContentTruncator locally to avoid circular dependency at module level
        from hermes.interface.assistant.deep_research_assistant.engine.context.content_truncator import ContentTruncator
        # Pass the primitive tuples directly
        context = {
            "external_files_data": data.external_files, # Tuple[PrimitiveArtifactData]
            "node_artifacts_data": data.node_artifacts, # Tuple[PrimitiveArtifactData]
            "truncator": ContentTruncator, # Pass the class
        }
        return self._render_template(context)


class ProblemHierarchyRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/problem_hierarchy.mako")

    def render(self, data: "ProblemHierarchyData", future_changes: int) -> str:
        # Pass the pre-rendered string and title
        context = {
            "file_system_hierarchy_str": data.file_system_hierarchy_str,
            "target_node_title": data.target_node_title # Pass title instead of node
        }
        return self._render_template(context)


class CriteriaSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/criteria.mako")

    def render(self, data: "CriteriaSectionData", future_changes: int) -> str:
        # Pass the primitive tuples
        context = {
            "criteria_list": data.criteria, # Tuple[str]
            "criteria_done_list": data.criteria_done, # Tuple[bool]
        }
        return self._render_template(context)


class SubproblemsSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/subproblems.mako")

    def render(self, data: "SubproblemsSectionData", future_changes: int) -> str:
        # Pass the primitive tuple of subproblem data
        context = {"subproblems_data": data.subproblems} # Tuple[PrimitiveSubproblemData]
        return self._render_template(context)


class ProblemPathHierarchyRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/problem_path_hierarchy.mako")

    def render(self, data: "ProblemPathHierarchyData", future_changes: int) -> str:
        # Pass the primitive tuple of path node data
        context = {"path_nodes_data": data.path_nodes} # Tuple[PrimitiveNodePathData]
        return self._render_template(context)


class KnowledgeBaseRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/knowledge_base.mako")

    def render(self, data: "KnowledgeBaseData", future_changes: int) -> str:
        # --- Apply future_changes logic ---
        if future_changes > 0:
            # If the knowledge base changes later, don't show the old version.
            # Return a note or an empty string.
            return "<knowledge_base>\n[Knowledge Base content omitted as it was updated later in the conversation.]\n</knowledge_base>"
            # Alternatively, return "" if we want it completely hidden.

        # Pass the primitive tuple of knowledge entry data
        context = {"knowledge_entries_data": data.knowledge_entries} # Tuple[PrimitiveKnowledgeEntryData]
        return self._render_template(context)


class GoalSectionRenderer(DynamicSectionRenderer):
    def __init__(self, template_manager: "TemplateManager"):
        super().__init__(template_manager, "sections/dynamic/goal.mako")

    def render(self, data: "GoalSectionData", future_changes: int) -> str:
        # Goal is static, doesn't change based on data or future changes
        return self._render_template({})
