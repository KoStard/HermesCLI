from hermes.chat.interface.assistant.deep_research.research import Research, ResearchNode
from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact
from hermes.chat.interface.commands.command import CommandRegistry
from hermes.chat.interface.commands.help_generator import CommandHelpGenerator
from hermes.chat.interface.templates.template_manager import TemplateManager

from . import AssistantInterface
from .dynamic_sections import DynamicSectionData
from .dynamic_sections.artifacts import ArtifactsSectionData
from .dynamic_sections.budget import BudgetSectionData
from .dynamic_sections.criteria import CriteriaSectionData
from .dynamic_sections.goal import GoalSectionData
from .dynamic_sections.header import HeaderSectionData
from .dynamic_sections.knowledge_base import KnowledgeBaseData
from .dynamic_sections.permanent_logs import PermanentLogsData
from .dynamic_sections.problem_definition import ProblemDefinitionData
from .dynamic_sections.problem_hierarchy import ProblemHierarchyData
from .dynamic_sections.problem_path_hierarchy import ProblemPathHierarchyData
from .dynamic_sections.subproblems import SubproblemsSectionData

# Define the consistent order of dynamic sections using the imported types
DYNAMIC_SECTION_ORDER: list[type[DynamicSectionData]] = [
    HeaderSectionData,
    ProblemDefinitionData,
    PermanentLogsData,
    BudgetSectionData,
    ArtifactsSectionData,
    ProblemHierarchyData,
    CriteriaSectionData,
    SubproblemsSectionData,
    ProblemPathHierarchyData,
    KnowledgeBaseData,
    GoalSectionData,
]


class DeepResearcherInterface(AssistantInterface):
    """Responsible for rendering interface content as strings.
    This class handles all string formatting and presentation logic.
    """

    def __init__(
        self,
        template_manager: TemplateManager,
        commands_help_generator: CommandHelpGenerator,
        command_registry: CommandRegistry,
    ):
        self.template_manager = template_manager
        self.commands_help_generator = commands_help_generator
        self.command_registry = command_registry

    def _get_parent_chain(self, node: ResearchNode | None) -> list[ResearchNode]:
        """Helper to get the parent chain including the given node"""
        if not node:
            return []
        chain = []
        current = node
        while current:
            chain.append(current)
            current = current.get_parent()
        return list(reversed(chain))

    def render_problem_defined(
        self,
        research: Research,
        target_node: ResearchNode,
        permanent_logs: list[str],
        budget: int | None,
        remaining_budget: int | None,
    ) -> tuple[str, list[DynamicSectionData]]:
        """Prepare the interface content when a problem is defined.

        Returns:
            A tuple containing:
            - static_content (str): Fixed interface content that doesn't change.
            - dynamic_sections_data (List[DynamicSectionData]): List of data objects
              representing the state of each dynamic section, in a consistent order.
        """
        # Render static content (remains the same)
        static_content = self._render_static_content(target_node)

        # Gather data for dynamic sections
        dynamic_sections_data = self._gather_dynamic_section_data(
            research=research,
            target_node=target_node,
            permanent_logs=permanent_logs,
            budget=budget,
            remaining_budget=remaining_budget,
        )
        return static_content, dynamic_sections_data

    def _render_static_content(self, target_node: ResearchNode) -> str:
        """Render the static content by rendering the main static.mako template."""
        # Get commands to pass to the template context
        commands = self.command_registry.get_all_commands()

        context = {
            "target_node": target_node,
            "commands": commands,  # Pass the commands dictionary directly
            "commands_help_content": self._generate_command_help(),
        }

        return self.template_manager.render_template("research_static.mako", **context)

    def _gather_dynamic_section_data(
        self,
        research: Research,
        target_node: ResearchNode,
        permanent_logs: list[str],
        budget: int | None,
        remaining_budget: int | None,
    ) -> list[DynamicSectionData]:
        """Gathers data required for each dynamic section and returns a list of data objects."""
        all_data = self._create_basic_section_data(target_node, permanent_logs, budget, remaining_budget)
        self._add_artifacts_data(all_data, research, target_node)
        self._add_hierarchy_and_criteria_data(all_data, research, target_node)
        self._add_knowledge_base_data(all_data, research)
        return self._order_and_validate_data(all_data)

    def _create_basic_section_data(
        self,
        target_node: ResearchNode,
        permanent_logs: list[str],
        budget: int | None,
        remaining_budget: int | None,
    ) -> dict:
        """Create basic section data that doesn't require complex processing"""
        return {
            HeaderSectionData: HeaderSectionData(),
            ProblemDefinitionData: ProblemDefinitionData.from_node(target_node=target_node),
            PermanentLogsData: PermanentLogsData(permanent_logs=permanent_logs),
            BudgetSectionData: BudgetSectionData(budget=budget, remaining_budget=remaining_budget),
            GoalSectionData: GoalSectionData(),
        }

    def _add_artifacts_data(self, all_data: dict, research: Research, target_node: ResearchNode) -> None:
        """Add artifacts data to the section data collection"""
        node_artifacts_list = self._collect_node_artifacts(research, target_node)
        self._add_external_research_artifacts(node_artifacts_list, research, target_node)
        external_files = research.get_external_file_manager().get_external_files()

        all_data[ArtifactsSectionData] = ArtifactsSectionData.from_artifact_lists(
            external_files_dict=external_files,
            node_artifacts_list=node_artifacts_list,
        )

    def _collect_node_artifacts(self, research: Research, target_node: ResearchNode) -> list:
        """Collect artifacts from the current research node tree"""
        root_node = research.get_root_node() if research.has_root_problem_defined() else target_node
        return self.collect_artifacts_recursively(root_node, target_node) if root_node else []

    def _add_external_research_artifacts(self, node_artifacts_list: list, research: Research, target_node: ResearchNode) -> None:
        """Add root-level artifacts from other research instances"""
        parent_repo = research.get_repo()
        if not parent_repo:
            return

        # Only get root-level artifacts from other research instances
        root_artifacts = parent_repo.get_root_artifacts_from_other_research_instances(research)
        for research_name, root_node, artifact in root_artifacts:
            is_fully_visible = target_node.get_artifact_status(artifact)
            # Include research_name to distinguish cross-root artifacts
            node_artifacts_list.append((root_node, artifact, is_fully_visible, research_name))

    def _add_hierarchy_and_criteria_data(self, all_data: dict, research: Research, target_node: ResearchNode) -> None:
        """Add hierarchy and criteria related data"""
        all_data[ProblemHierarchyData] = ProblemHierarchyData.from_research_node(
            target_node=target_node,
            root_node=research.get_root_node(),
        )
        all_data[CriteriaSectionData] = CriteriaSectionData.from_node(target_node=target_node)
        all_data[SubproblemsSectionData] = SubproblemsSectionData.from_node(target_node=target_node)

        parent_chain = self._get_parent_chain(target_node)
        all_data[ProblemPathHierarchyData] = ProblemPathHierarchyData.from_parent_chain(
            parent_chain=parent_chain,
            current_node=target_node,
        )

    def _add_knowledge_base_data(self, all_data: dict, research: Research) -> None:
        """Add knowledge base data"""
        knowledge_base = research.get_knowledge_base()
        all_data[KnowledgeBaseData] = KnowledgeBaseData.from_knowledge_base(knowledge_base=knowledge_base)

    def _order_and_validate_data(self, all_data: dict) -> list[DynamicSectionData]:
        """Order data according to defined order and validate completeness"""
        ordered_data = [all_data[section_type] for section_type in DYNAMIC_SECTION_ORDER if section_type in all_data]

        if len(ordered_data) != len(DYNAMIC_SECTION_ORDER):
            print("Warning: Mismatch between expected dynamic sections and gathered data.")

        return ordered_data

    def collect_artifacts_recursively(
        self, node: ResearchNode, current_node: ResearchNode
    ) -> list[tuple[ResearchNode, Artifact, bool, str | None]]:
        """Recursively collect artifacts from a node and all its descendants.

        Args:
            node: The node to collect artifacts from
            current_node: The node currently being viewed (for visibility checks)

        Returns:
            List of tuples: (owner ResearchNode, Artifact, is_visible_to_current_node, research_name)
        """
        artifacts = []
        if not node:
            return artifacts

        # Add this node's artifacts
        for artifact in node.get_artifacts():
            if artifact.is_external:
                continue
            is_fully_visible = current_node.get_artifact_status(artifact)

            artifacts.append((node, artifact, is_fully_visible, None))

        # Recursively collect artifacts from all child nodes
        for child_node in node.list_child_nodes():
            artifacts.extend(self.collect_artifacts_recursively(child_node, current_node))

        return artifacts

    def _generate_command_help(self) -> str:
        """Generate help text for all registered commands by rendering the command_help template."""
        # Get all registered commands suitable for the problem-defined interface
        commands = self.command_registry.get_all_commands()

        return self.commands_help_generator.generate_help(commands)
