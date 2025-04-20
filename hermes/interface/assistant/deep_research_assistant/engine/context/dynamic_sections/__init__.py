from typing import Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    # Import base classes for type hinting
    from .base import DynamicSectionData, DynamicSectionRenderer
    from hermes.interface.assistant.deep_research_assistant.engine.templates.template_manager import TemplateManager


# Type alias for the registry
RendererRegistry = Dict[Type["DynamicSectionData"], "DynamicSectionRenderer"]


def create_renderer_registry(template_manager: "TemplateManager") -> RendererRegistry:
    """Creates and populates the registry mapping data types to renderer instances."""
    # Import Data and Renderer classes from their respective section modules
    from .header import HeaderSectionData, HeaderSectionRenderer
    from .permanent_logs import PermanentLogsData, PermanentLogsRenderer
    from .budget import BudgetSectionData, BudgetSectionRenderer
    from .artifacts import ArtifactsSectionData, ArtifactsSectionRenderer
    from .problem_hierarchy import ProblemHierarchyData, ProblemHierarchyRenderer
    from .criteria import CriteriaSectionData, CriteriaSectionRenderer
    from .subproblems import SubproblemsSectionData, SubproblemsSectionRenderer
    from .problem_path_hierarchy import ProblemPathHierarchyData, ProblemPathHierarchyRenderer
    from .knowledge_base import KnowledgeBaseData, KnowledgeBaseRenderer
    from .goal import GoalSectionData, GoalSectionRenderer

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
