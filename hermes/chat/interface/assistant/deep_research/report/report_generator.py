from typing import TYPE_CHECKING, Any

from hermes.chat.interface.assistant.deep_research.context import AssistantInterface
from hermes.chat.interface.assistant.deep_research.report import BudgetInfo, ReportGenerator
from hermes.chat.interface.templates.template_manager import TemplateManager

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import Research, ResearchNode


class ReportGeneratorImpl(ReportGenerator):
    """Responsible for generating reports based on the research data using Mako templates."""

    def __init__(self, template_manager: TemplateManager):
        """Initialize ReportGenerator.

        Args:
            research: The Research instance containing research data.
            template_manager: An instance of TemplateManager to render templates.
        """
        self.template_manager = template_manager

    def generate_final_report(
        self,
        research: "Research",
        interface: AssistantInterface,
        root_completion_message: str | None = None,
        budget_info: BudgetInfo | None = None,
    ) -> str:
        """Generate a summary of all artifacts created during the research using a template.

        Args:
            research: The Research instance containing the research data.
            interface: The DeepResearcherInterface instance (needed for _collect_artifacts_recursively).
                       Consider refactoring _collect_artifacts_recursively into FileSystem or a utility
                       to remove this dependency if possible in the future.
            root_completion_message: Optional final message from the root node.
            budget_info: Optional budget information to include in the report.

        Returns:
            A string containing the formatted final report.
        """
        root_node = research.get_root_node()
        artifacts_by_problem = self._collect_artifacts_by_problem(root_node, research, interface)

        # Convert budget info to dictionary if provided, otherwise use empty dict
        budget_data = budget_info.to_dict() if budget_info else {}

        context = self._build_template_context(root_node, artifacts_by_problem, root_completion_message, budget_data)
        return self._render_report_with_fallback(context)

    def _collect_artifacts_by_problem(
        self, root_node: "ResearchNode", research: "Research", interface: AssistantInterface
    ) -> dict[str, list[dict[str, str]]]:
        """Collect and group artifacts by problem title"""
        artifacts_by_problem: dict[str, list[dict[str, str]]] = {}

        if not root_node:
            return artifacts_by_problem

        all_artifacts = interface.collect_artifacts_recursively(root_node, root_node)
        if not all_artifacts:
            return artifacts_by_problem

        for node, artifact, _ in all_artifacts:
            owner_title = node.get_title()
            if owner_title not in artifacts_by_problem:
                artifacts_by_problem[owner_title] = []

            # Get the relative path from Results directory for this artifact
            artifact_info = {"name": artifact.name, "relative_path": self._get_artifact_relative_path(node, research, artifact.name)}
            artifacts_by_problem[owner_title].append(artifact_info)

        return artifacts_by_problem

    def _get_artifact_relative_path(self, node: "ResearchNode", research: "Research", artifact_name: str) -> str:
        """Get the relative path from project root for the artifact"""
        node_path = node.get_path()
        if not node_path:
            # Root level artifact
            return f"Results/{artifact_name}.md"

        # Use the dual directory file system to get the correct artifact directory
        dual_fs = research.get_dual_directory_fs()

        artifact_dir = dual_fs.get_artifact_directory_for_node_path(node_path)

        # Get relative path from the project root
        project_root = dual_fs.root_directory
        relative_dir = artifact_dir.relative_to(project_root)

        return f"{relative_dir}/{artifact_name}.md"

    def _build_template_context(
        self,
        root_node: "ResearchNode",
        artifacts_by_problem: dict[str, list[dict[str, str]]],
        root_completion_message: str | None,
        budget_info: dict[str, int | None] = None,
    ) -> dict[str, Any]:
        """Build context dictionary for template rendering"""
        return {
            "root_node": root_node,
            "artifacts_by_problem": artifacts_by_problem if artifacts_by_problem else None,
            "root_completion_message": root_completion_message,
            "budget_info": budget_info,
        }

    def _render_report_with_fallback(
        self,
        context: dict[str, Any],
    ) -> str:
        """Render report template with fallback error handling"""
        return self.template_manager.render_template("report/final_report.mako", **context)
