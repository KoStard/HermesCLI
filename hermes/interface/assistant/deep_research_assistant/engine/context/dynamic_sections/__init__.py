from typing import Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .data import DynamicSectionData
    from .renderers import DynamicSectionRenderer
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager


# Type alias for the registry
RendererRegistry = Dict[Type["DynamicSectionData"], "DynamicSectionRenderer"]


def create_renderer_registry(template_manager: "TemplateManager") -> RendererRegistry:
    """Creates and populates the registry mapping data types to renderer instances."""
    from .data import (
        HeaderSectionData, PermanentLogsData, BudgetSectionData, ArtifactsSectionData,
        ProblemHierarchyData, CriteriaSectionData, SubproblemsSectionData,
        ProblemPathHierarchyData, KnowledgeBaseData, GoalSectionData
    )
    from .renderers import (
        HeaderSectionRenderer, PermanentLogsRenderer, BudgetSectionRenderer, ArtifactsSectionRenderer,
        ProblemHierarchyRenderer, CriteriaSectionRenderer, SubproblemsSectionRenderer,
        ProblemPathHierarchyRenderer, KnowledgeBaseRenderer, GoalSectionRenderer
    )

    registry: RendererRegistry = {
        HeaderSectionData: HeaderSectionRenderer(template_manager),
        PermanentLogsData: PermanentLogsRenderer(template_manager),
        BudgetSectionData: BudgetSectionRenderer(template_manager),
        ArtifactsSectionData: ArtifactsSectionRenderer(template_manager),
        ProblemHierarchyData: ProblemHierarchyRenderer(template_manager),
        CriteriaSectionData: CriteriaSectionRenderer(template_manager),
        SubproblemsSectionData: SubproblemsSectionRenderer(template_manager),
        ProblemPathHierarchyData: ProblemPathHierarchyRenderer(template_manager),
        KnowledgeBaseData: KnowledgeBaseRenderer(template_manager),
        GoalSectionData: GoalSectionRenderer(template_manager),
    }
    return registry
