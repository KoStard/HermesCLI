from typing import Any

from hermes.chat.interface.assistant.deep_research.commands.command_context import ResearchCommandContextImpl
from hermes.chat.interface.commands.command import Command as BaseCommand


class OpenArtifactCommand(BaseCommand[ResearchCommandContextImpl, None]):
    def __init__(self):
        super().__init__(
            "open_artifact",
            (
                "Open an artifact to view its full content. Artifacts automatically close after 5 message iterations. "
                "Optionally specify root_problem to search artifacts from other root problems."
            ),
        )
        self.add_section("name", True, "Name of the artifact to open")
        self.add_section(
            "root_problem", False, "Optional: Name of the root problem to search artifacts from (for cross-root artifact access)"
        )

    def execute(self, context: ResearchCommandContextImpl, args: dict[str, Any]) -> None:
        """Execute the command to open an artifact"""
        artifact_name = args["name"]

        root_problem = args.get("root_problem")

        if root_problem and root_problem != context.research_project.get_root_node().get_title():
            self._open_cross_root_artifact(context, args, artifact_name, root_problem)
        else:
            self._open_current_research_artifact(context, args, artifact_name)

    def _open_cross_root_artifact(
        self, context: ResearchCommandContextImpl, args: dict[str, Any], artifact_name: str, root_problem: str
    ) -> None:
        """Open artifact from a specific root problem"""
        cross_root_results = context.search_cross_root_artifacts(artifact_name, root_problem)
        if cross_root_results:
            # For cross-root artifacts, set status on the owning node
            for _research_name, _node, artifact in cross_root_results:
                context.current_node.set_artifact_status(artifact, True)

            context.add_command_output(
                self.name,
                args,
                f"Artifact '{artifact_name}' from root problem '{root_problem}' is now fully visible.",
            )
        else:
            context.add_command_output(
                self.name,
                args,
                f"No artifact named '{artifact_name}' found in root problem '{root_problem}'.",
            )

    def _open_current_research_artifact(self, context: ResearchCommandContextImpl, args: dict[str, Any], artifact_name: str):
        current_node = context.current_node
        node_and_artifacts = context.search_artifacts(artifact_name)

        for _, artifact in node_and_artifacts:
            current_node.set_artifact_status(artifact, True)

        if node_and_artifacts:
            context.add_command_output(
                self.name,
                args,
                f"Artifact '{artifact_name}' is now fully visible.",
            )
        else:
            context.add_command_output(
                self.name,
                args,
                f"No artifact named '{artifact_name}' found in current research project.",
            )
