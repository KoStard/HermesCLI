from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.assistant.deep_research.research.research_node_component.artifact import Artifact
from hermes.chat.interface.commands.command import Command


class OverwriteArtifactCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "overwrite_artifact",
            "Overwrite an existing artifact's content and/or summary. At least one must be specified.",
        )
        self.add_section("name", True, "Name of the artifact to overwrite")
        self.add_section("content", False, "New content for the artifact (optional if summary is changed)")
        self.add_section("short_summary", False, "New short summary for the artifact (optional if content is changed)")

    def validate(self, args: dict[str, Any]) -> list[str]:
        errors = super().validate(args)

        # Either content or short_summary must be provided
        if "content" not in args and "short_summary" not in args:
            errors.append("Either content or short_summary must be provided")

        return errors

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Overwrite an existing artifact's content and/or summary"""
        artifact_name = args["name"]

        # Find and validate artifact
        artifact = self._find_artifact(context, args, artifact_name)
        if artifact is None:
            return

        # Update artifact content and/or summary
        changes = self._update_artifact(artifact, args)

        # Save artifact and provide confirmation
        artifact.save()
        self._add_confirmation(context, args, artifact_name, changes)

    def _find_artifact(self, context: ResearchCommandContextImpl, args: dict, artifact_name: str) -> Artifact | None:
        """Find and validate an artifact by name."""
        current_node = context.current_node
        matching_artifacts = [a for a in current_node.get_artifacts() if a.name == artifact_name]

        if not matching_artifacts:
            context.add_command_output(self.name, args, f"Error: Artifact '{artifact_name}' not found.")
            return None

        artifact = matching_artifacts[0]

        # Check if this is an external artifact
        if artifact.is_external:
            context.add_command_output(self.name, args, f"Error: Cannot modify external artifact '{artifact_name}'.")
            return None

        return artifact

    def _update_artifact(self, artifact: Artifact, args: dict) -> list[str]:
        """Update artifact content and/or summary and return a list of what was changed."""
        changes = []

        # Update content if provided
        if "content" in args:
            artifact.update_content(args["content"])
            changes.append("content")

        # Update summary if provided
        if "short_summary" in args:
            artifact.update_short_summary(args["short_summary"])
            changes.append("summary")

        return changes

    def _add_confirmation(self, context: ResearchCommandContextImpl, args: dict, artifact_name: str, changes: list[str]) -> None:
        """Add a confirmation message about the changes made."""
        context.add_command_output(
            self.name,
            args,
            f"Artifact '{artifact_name}' updated with new {' and '.join(changes)}."
        )
