from .file_system import FileSystem


class ReportGenerator:
    """
    Responsible for generating reports based on the research data.
    This class handles all report formatting and generation.
    """

    def __init__(self, file_system: FileSystem):
        self.file_system = file_system

    def generate_final_report(self, interface) -> str:
        """Generate a summary of all artifacts created during the research"""
        if not self.file_system.root_node:
            return "Research completed, but no artifacts were generated."

        # Collect all artifacts from the entire problem hierarchy
        all_artifacts = interface.collect_artifacts_recursively(
            self.file_system.root_node, self.file_system.root_node
        )

        if not all_artifacts:
            return "Research completed, but no artifacts were generated."

        # Group artifacts by problem
        artifacts_by_problem = {}
        for owner_title, name, content, is_visible in all_artifacts:
            if owner_title not in artifacts_by_problem:
                artifacts_by_problem[owner_title] = []
            artifacts_by_problem[owner_title].append(name)

        # Generate the report
        result = f"""# Deep Research Completed

## Problem: {self.file_system.root_node.title}

## Summary of Generated Artifacts

The research has been completed and the following artifacts have been created:

"""

        # List all artifacts with their filepaths
        for problem_title, artifact_names in artifacts_by_problem.items():
            result += f"### {problem_title}\n\n"
            for name in artifact_names:
                # Construct the relative filepath, ensuring .md extension
                filepath = f"Artifacts/{name}.md"
                result += f"- `{filepath}`: {name}\n"
            result += "\n"

        result += """
These artifacts contain the valuable outputs of the research process. Each artifact represents
a concrete piece of knowledge or analysis that contributes to solving the root problem.
"""

        return result
