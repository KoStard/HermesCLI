from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command


class DeleteArtifactCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "delete_artifact",
            "Delete an existing artifact",
        )
        self.add_section("name", True, "Name of the artifact to delete")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Delete an existing artifact"""
        current_node = context.current_node
        artifact_name = args["name"]

        # Find the artifact with the given name
        matching_artifacts = [a for a in current_node.get_artifacts() if a.name == artifact_name]

        if not matching_artifacts:
            context.add_command_output(self.name, args, f"Error: Artifact '{artifact_name}' not found.")
            return

        artifact = matching_artifacts[0]

        # Check if this is an external artifact
        if artifact.is_external:
            context.add_command_output(self.name, args, f"Error: Cannot delete external artifact '{artifact_name}'.")
            return

        # Remove the artifact
        success = current_node.get_artifact_manager().remove_artifact(artifact)

        if success:
            context.add_command_output(self.name, args, f"Artifact '{artifact_name}' successfully deleted.")
        else:
            context.add_command_output(self.name, args, f"Error: Failed to delete artifact '{artifact_name}'.")
