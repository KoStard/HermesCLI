from hermes.chat.interface.assistant.deep_research_assistant.engine.research import Research
from hermes.chat.interface.templates.template_manager import TemplateManager


class ReportGenerator:
    """
    Responsible for generating reports based on the research data using Mako templates.
    """

    def __init__(self, research: Research, template_manager: TemplateManager):
        """
        Initialize ReportGenerator.

        Args:
            research: The Research instance containing research data.
            template_manager: An instance of TemplateManager to render templates.
        """
        self.research = research
        self.template_manager = template_manager

    def generate_final_report(self, interface, root_completion_message: str | None = None) -> str:
        """
        Generate a summary of all artifacts created during the research using a template.

        Args:
            interface: The DeepResearcherInterface instance (needed for _collect_artifacts_recursively).
                       Consider refactoring _collect_artifacts_recursively into FileSystem or a utility
                       to remove this dependency if possible in the future.
            root_completion_message: Optional final message from the root node.

        Returns:
            A string containing the formatted final report.
        """
        root_node = self.research.get_root_node()
        artifacts_by_problem: dict[str, list[str]] = {}

        if root_node:
            # Collect all artifacts from the entire problem hierarchy
            # Use the interface's helper for collecting artifacts
            all_artifacts = interface._collect_artifacts_recursively(
                root_node,
                root_node,  # Pass root twice for initial call
            )

            if all_artifacts:
                # Group artifact names by problem title
                for owner_title, name, _, _ in all_artifacts:
                    if owner_title not in artifacts_by_problem:
                        artifacts_by_problem[owner_title] = []
                    artifacts_by_problem[owner_title].append(name)

        # Prepare context for the template
        context = {
            "root_node": root_node,
            "artifacts_by_problem": artifacts_by_problem if artifacts_by_problem else None,
            "root_completion_message": root_completion_message,  # Add the message to the context
        }

        try:
            # Render the final report template
            return self.template_manager.render_template("report/final_report.mako", **context)
        except Exception as e:
            print(f"Error generating final report: {e}")
            # Return a fallback error message
            fallback_report = "# Deep Research Report Generation Failed\n\n"
            fallback_report += f"An error occurred while generating the final report: {e}\n"
            if root_node:
                fallback_report += f"Root Problem: {root_node.get_title()}\n"
            if artifacts_by_problem:
                fallback_report += f"Found artifacts for {len(artifacts_by_problem)} problems.\n"
            return fallback_report
