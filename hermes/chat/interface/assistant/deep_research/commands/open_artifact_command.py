from typing import Any

from hermes.chat.interface.commands.command import Command as BaseCommand
from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl


class OpenArtifactCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "open_artifact",
            "Open an artifact to view its full content. Artifacts automatically close after 5 message iterations.",
        )
        self.add_section("name", True, "Name of the artifact to open")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Execute the command to open an artifact"""
        artifact_name = args["name"]

        # Find the artifact in the current node or its ancestors
        current_node = context.current_node

        node_and_artifacts = context.search_artifacts(artifact_name)

        for _, artifact in node_and_artifacts:
            current_node.set_artifact_status(artifact, True)

        context.add_command_output(
            self.name,
            args,
            f"Artifact '{artifact_name}' is now fully visible.",
        )
