from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import base classes for type hinting
    from hermes.chat.interface.templates.template_manager import TemplateManager

    from . import DynamicSectionData, DynamicSectionRenderer


# Type alias for the registry
RendererRegistry = dict[type["DynamicSectionData"], "DynamicSectionRenderer"]


def create_renderer_registry(template_manager: "TemplateManager") -> RendererRegistry:
    """Creates and populates the registry mapping data types to renderer instances."""
    # Import Data and Renderer classes from their respective section modules
    from .artifacts import ArtifactsSectionData, ArtifactsSectionRenderer
    from .budget import BudgetSectionData, BudgetSectionRenderer
    from .criteria import CriteriaSectionData, CriteriaSectionRenderer
    from .goal import GoalSectionData, GoalSectionRenderer
    from .header import HeaderSectionData, HeaderSectionRenderer
    from .knowledge_base import KnowledgeBaseData, KnowledgeBaseRenderer
    from .permanent_logs import PermanentLogsData, PermanentLogsRenderer
    from .problem_hierarchy import ProblemHierarchyData, ProblemHierarchyRenderer
    from .problem_path_hierarchy import (
        ProblemPathHierarchyData,
        ProblemPathHierarchyRenderer,
    )
    from .subproblems import SubproblemsSectionData, SubproblemsSectionRenderer

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
