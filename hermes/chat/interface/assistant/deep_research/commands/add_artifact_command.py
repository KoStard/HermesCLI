from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact
from hermes.chat.interface.commands.command import Command


class AddArtifactCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "add_artifact",
            "Add an artifact to the current problem. Artifacts are closed by default and show only the summary. "
            "Keep content ~1 page long unless specifically requested to be longer. "
            "Use descriptive names that clearly indicate purpose.",
        )
        self.add_section("name", True, "Name of the artifact (use descriptive names like 'Market_Analysis_Summary' not 'Doc1')")
        self.add_section("content", True, "Content of the artifact (keep to ~1 page unless specifically requested to be longer)")
        self.add_section(
            "short_summary",
            True,
            "Short summary of the artifact. Can be 1-2 paragraphs, should call out what's important in this artifact.",
        )

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Add an artifact to the current problem"""
        current_node = context.current_node

        artifact = Artifact(
            name=args["name"],
            content=args["content"],
            short_summary=args["short_summary"],
            is_external=False,
        )
        current_node.add_artifact(artifact)

        # Add confirmation output
        context.add_command_output(self.name, args, f"Artifact '{args['name']}' added.")
