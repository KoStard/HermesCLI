from hermes.chat.interface.assistant.deep_research.context import AssistantInterface
from hermes.chat.interface.assistant.deep_research.report import ReportGenerator
from hermes.chat.interface.assistant.deep_research.research import Research
from hermes.chat.interface.templates.template_manager import TemplateManager


class ReportGeneratorImpl(ReportGenerator):
    """Responsible for generating reports based on the research data using Mako templates.
    """

    def __init__(self, template_manager: TemplateManager):
        """Initialize ReportGenerator.

        Args:
            research: The Research instance containing research data.
            template_manager: An instance of TemplateManager to render templates.
        """
        self.template_manager = template_manager

    def generate_final_report(self, research: Research, interface: AssistantInterface, root_completion_message: str | None = None) -> str:
        """Generate a summary of all artifacts created during the research using a template.

        Args:
            interface: The DeepResearcherInterface instance (needed for _collect_artifacts_recursively).
                       Consider refactoring _collect_artifacts_recursively into FileSystem or a utility
                       to remove this dependency if possible in the future.
            root_completion_message: Optional final message from the root node.

        Returns:
            A string containing the formatted final report.
        """
        root_node = research.get_root_node()
        artifacts_by_problem = self._collect_artifacts_by_problem(root_node, interface)
        context = self._build_template_context(root_node, artifacts_by_problem, root_completion_message)
        return self._render_report_with_fallback(context, root_node, artifacts_by_problem)

    def _collect_artifacts_by_problem(self, root_node, interface: AssistantInterface) -> dict[str, list[str]]:
        """Collect and group artifacts by problem title"""
        artifacts_by_problem: dict[str, list[str]] = {}

        if not root_node:
            return artifacts_by_problem

        all_artifacts = interface._collect_artifacts_recursively(root_node, root_node)
        if not all_artifacts:
            return artifacts_by_problem

        for node, artifact, _ in all_artifacts:
            owner_title = node.get_title()
            if owner_title not in artifacts_by_problem:
                artifacts_by_problem[owner_title] = []
            artifacts_by_problem[owner_title].append(artifact.name)

        return artifacts_by_problem

    def _build_template_context(self, root_node, artifacts_by_problem: dict, root_completion_message: str | None) -> dict:
        """Build context dictionary for template rendering"""
        return {
            "root_node": root_node,
            "artifacts_by_problem": artifacts_by_problem if artifacts_by_problem else None,
            "root_completion_message": root_completion_message,
        }

    def _render_report_with_fallback(self, context: dict, root_node, artifacts_by_problem: dict) -> str:
        """Render report template with fallback error handling"""
        try:
            return self.template_manager.render_template("report/final_report.mako", **context)
        except Exception as e:
            return self._create_fallback_report(e, root_node, artifacts_by_problem)

    def _create_fallback_report(self, error: Exception, root_node, artifacts_by_problem: dict) -> str:
        """Create fallback report when template rendering fails"""
        print(f"Error generating final report: {error}")
        fallback_report = "# Deep Research Report Generation Failed\n\n"
        fallback_report += f"An error occurred while generating the final report: {error}\n"

        if root_node:
            fallback_report += f"Root Problem: {root_node.get_title()}\n"
        if artifacts_by_problem:
            fallback_report += f"Found artifacts for {len(artifacts_by_problem)} problems.\n"

        return fallback_report
