from typing import TYPE_CHECKING

from . import DynamicSectionData

if TYPE_CHECKING:
    from hermes.chat.interface.templates.template_manager import TemplateManager

    from . import DynamicSectionRenderer


# Type alias for the registry
DynamicDataTypeToRendererMap = dict[type["DynamicSectionData"], "DynamicSectionRenderer"]


def register_all_dynamic_section_types() -> None:
    """Register all dynamic section data types in the DynamicSectionData registry."""
    from .artifacts import ArtifactsSectionData
    from .budget import BudgetSectionData
    from .criteria import CriteriaSectionData
    from .goal import GoalSectionData
    from .header import HeaderSectionData
    from .knowledge_base import KnowledgeBaseData
    from .permanent_logs import PermanentLogsData
    from .problem_hierarchy import ProblemHierarchyData
    from .problem_path_hierarchy import ProblemPathHierarchyData
    from .subproblems import SubproblemsSectionData

    # Register all concrete DynamicSectionData types
    DynamicSectionData.register_type(HeaderSectionData)
    DynamicSectionData.register_type(PermanentLogsData)
    DynamicSectionData.register_type(BudgetSectionData)
    DynamicSectionData.register_type(ArtifactsSectionData)
    DynamicSectionData.register_type(CriteriaSectionData)
    DynamicSectionData.register_type(GoalSectionData)
    DynamicSectionData.register_type(KnowledgeBaseData)
    DynamicSectionData.register_type(ProblemHierarchyData)
    DynamicSectionData.register_type(ProblemPathHierarchyData)
    DynamicSectionData.register_type(SubproblemsSectionData)


def get_data_type_to_renderer_instance_map(template_manager: "TemplateManager") -> DynamicDataTypeToRendererMap:
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

    registry: DynamicDataTypeToRendererMap = {
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
