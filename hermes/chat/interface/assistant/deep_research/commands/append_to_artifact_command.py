from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command


class AppendToArtifactCommand(Command[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "append_to_artifact",
            "Append content to an existing artifact",
        )
        self.add_section("name", True, "Name of the artifact to append to")
        self.add_section("content", True, "Content to append to the artifact")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Append content to an existing artifact"""
        current_node = context.current_node
        artifact_name = args["name"]
        content_to_append = args["content"]

        # Find the artifact with the given name
        matching_artifacts = [a for a in current_node.get_artifacts() if a.name == artifact_name]

        if not matching_artifacts:
            context.add_command_output(self.name, args, f"Error: Artifact '{artifact_name}' not found.")
            return

        artifact = matching_artifacts[0]

        # Check if this is an external artifact
        if artifact.is_external:
            context.add_command_output(self.name, args, f"Error: Cannot modify external artifact '{artifact_name}'.")
            return

        # Append content
        artifact.append_content(content_to_append)

        # Save the updated artifact
        artifact.save()

        # Provide confirmation output
        context.add_command_output(
            self.name,
            args,
            f"Content successfully appended to artifact '{artifact_name}'."
        )
