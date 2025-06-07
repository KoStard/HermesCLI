from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.agent_old.framework.context.dynamic_sections import DynamicDataTypeToRendererMap

if TYPE_CHECKING:
    from hermes.chat.interface.templates.template_manager import TemplateManager


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
    from .problem_definition import ProblemDefinitionData, ProblemDefinitionRenderer
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
        ProblemDefinitionData: ProblemDefinitionRenderer(template_manager),
        CriteriaSectionData: CriteriaSectionRenderer(template_manager),
        SubproblemsSectionData: SubproblemsSectionRenderer(template_manager),
        ProblemPathHierarchyData: ProblemPathHierarchyRenderer(template_manager),
        KnowledgeBaseData: KnowledgeBaseRenderer(template_manager),
        GoalSectionData: GoalSectionRenderer(template_manager),
    }
    return registry
