from hermes.chat.interface.assistant.agent.framework.context import AgentInterface
from hermes.chat.interface.assistant.agent.framework.context.dynamic_sections import DynamicSectionData
from hermes.chat.interface.assistant.agent.framework.research import Research, ResearchNode
from hermes.chat.interface.assistant.agent.framework.research.research_node_component.artifact import Artifact
from hermes.chat.interface.commands.command import CommandRegistry
from hermes.chat.interface.commands.help_generator import CommandHelpGenerator
from hermes.chat.interface.templates.template_manager import TemplateManager

# Import base data class and specific section data classes/factories from their new locations
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

# Import types needed for factory methods (still required here for _gather_dynamic_section_data)

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


class DeepResearcherInterface(AgentInterface):
    """
    Responsible for rendering interface content as strings.
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
        """
        Prepare the interface content when a problem is defined.

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

        return self.template_manager.render_template("static.mako", **context)

    def _gather_dynamic_section_data(
        self,
        research: Research,
        target_node: ResearchNode,
        permanent_logs: list[str],
        budget: int | None,
        remaining_budget: int | None,
    ) -> list[DynamicSectionData]:
        """Gathers data required for each dynamic section and returns a list of data objects."""
        all_data = {}  # Store data keyed by type for easy access

        # --- Gather data for each section type ---

        # Header: No data needed
        all_data[HeaderSectionData] = HeaderSectionData()

        # Problem Definition - Use factory method
        all_data[ProblemDefinitionData] = ProblemDefinitionData.from_node(target_node=target_node)

        # Permanent Logs
        all_data[PermanentLogsData] = PermanentLogsData(permanent_logs=permanent_logs)

        # Budget
        all_data[BudgetSectionData] = BudgetSectionData(budget=budget, remaining_budget=remaining_budget)

        # Artifacts
        node_artifacts_list = []
        # Use target_node directly if root is not yet defined (e.g., during initial define_problem)
        root_node = research.get_root_node() if research.has_root_problem_defined() else target_node
        if root_node:
            node_artifacts_list = self._collect_artifacts_recursively(root_node, target_node)

        parent_repo = research.get_repo()
        if parent_repo:
            # Get artifacts from all research instances
            all_research_artifacts = parent_repo.get_all_artifacts()

            # Add artifacts from other research instances (marked as external)
            for research_name, artifacts in all_research_artifacts.items():
                # Skip current research instance
                if parent_repo.get_research(research_name) == research:
                    continue

                for node, artifact in artifacts:
                    node_artifacts_list.append((node, artifact, False))

        # Get external files from manager and convert to dict by name
        external_files = research.get_external_file_manager().get_external_files()

        # Use factory method for ArtifactsSectionData
        all_data[ArtifactsSectionData] = ArtifactsSectionData.from_artifact_lists(
            external_files_dict=external_files, node_artifacts_list=node_artifacts_list
        )

        # Problem Hierarchy (Short) - Use factory method
        all_data[ProblemHierarchyData] = ProblemHierarchyData.from_research_node(
            target_node=target_node, root_node=research.get_root_node()
        )

        # Criteria - Use factory method
        all_data[CriteriaSectionData] = CriteriaSectionData.from_node(target_node=target_node)

        # Subproblems - Use factory method
        all_data[SubproblemsSectionData] = SubproblemsSectionData.from_node(target_node=target_node)

        # Problem Path Hierarchy - Use factory method
        parent_chain = self._get_parent_chain(target_node)
        all_data[ProblemPathHierarchyData] = ProblemPathHierarchyData.from_parent_chain(parent_chain=parent_chain, current_node=target_node)

        # Knowledge Base - Use factory method
        knowledge_base = research.get_knowledge_base()
        all_data[KnowledgeBaseData] = KnowledgeBaseData.from_knowledge_base(knowledge_base=knowledge_base)

        # Goal: No data needed
        all_data[GoalSectionData] = GoalSectionData()

        # --- Return data objects in the defined order ---
        ordered_data = [all_data[section_type] for section_type in DYNAMIC_SECTION_ORDER if section_type in all_data]

        # Sanity check: Ensure all expected sections were populated
        if len(ordered_data) != len(DYNAMIC_SECTION_ORDER):
            print("Warning: Mismatch between expected dynamic sections and gathered data.")
            # Potentially raise an error or log more details

        return ordered_data

    def _collect_artifacts_recursively(self, node: ResearchNode, current_node: ResearchNode) -> list[tuple[ResearchNode, Artifact, bool]]:
        """
        Recursively collect artifacts from a node and all its descendants.

        Args:
            node: The node to collect artifacts from
            current_node: The node currently being viewed (for visibility checks)

        Returns:
            List of tuples: (owner ResearchNode, Artifact, is_visible_to_current_node)
        """
        artifacts = []
        if not node:
            return artifacts

        # Add this node's artifacts
        for artifact in node.get_artifacts():
            is_fully_visible = artifact.is_external
            is_fully_visible |= current_node.get_node_state().artifacts_status.get(artifact.name) or False

            artifacts.append((node, artifact, is_fully_visible))

        # Recursively collect artifacts from all child nodes
        for child_node in node.list_child_nodes():
            artifacts.extend(self._collect_artifacts_recursively(child_node, current_node))

        return artifacts

    def _generate_command_help(self) -> str:
        """Generate help text for all registered commands by rendering the command_help template."""
        # Get all registered commands suitable for the problem-defined interface
        commands = self.command_registry.get_all_commands()

        return self.commands_help_generator.generate_help(commands)
