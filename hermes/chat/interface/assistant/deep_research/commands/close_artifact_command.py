from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command as BaseCommand


class CloseArtifactCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "close_artifact",
            "Close an artifact manually, the short summary will remain visible. Artifacts also auto-close after 5 message iterations.",
        )
        self.add_section("name", True, "Name of the artifact to close")

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Execute the command to half-close an artifact"""
        artifact_name = args["name"]

        # Find the artifact in the current node or its ancestors
        current_node = context.current_node

        node_and_artifacts = context.search_artifacts(artifact_name)

        for _, artifact in node_and_artifacts:
            current_node.set_artifact_status(artifact, False)

        # For now, just report that the artifact is half-closed
        context.add_command_output(
            self.name,
            args,
            f"Artifact '{artifact_name}' is now closed (showing only the summary).",
        )
