from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode


@dataclass
class Artifact:
    name: str
    content: str
    short_summary: str
    is_external: bool = False

    @staticmethod
    def load_from_file(file_path: Path) -> "Artifact":
        """Load an artifact from a file"""
        md_file = MarkdownFileWithMetadataImpl.load_from_file(str(file_path))

        # Use name from metadata if present, otherwise use filename
        name = md_file.get_metadata().get("name", file_path.stem)
        summary = md_file.get_metadata().get("summary", "")

        return Artifact(
            name=name,
            content=md_file.get_content(),
            short_summary=summary,
            is_external=False  # File-based artifacts default to non-external
        )

    def save_to_file(self, directory_path: Path) -> None:
        """Save an artifact to a file with metadata"""
        md_file = MarkdownFileWithMetadataImpl(self.name, self.content)
        md_file.add_property("name", self.name)
        md_file.add_property("summary", self.short_summary)

        # Add is_external to metadata if true
        if self.is_external:
            md_file.add_property("is_external", True)

        # MarkdownFileWithMetadataImpl.save_file handles directory creation
        md_file.save_file(directory_path)

    def __str__(self) -> str:
        """String representation of the artifact"""
        return f"{self.name}: {self.short_summary}"


class ArtifactManager:
    """Manages artifacts for a research node"""

    def __init__(self, node: 'ResearchNode'):
        self.node = node
        self.artifacts: list[Artifact] = []

    @classmethod
    def load_for_research_node(cls, research_node: 'ResearchNode') -> list["ArtifactManager"]:
        """Load artifacts for a research node"""
        manager = cls(research_node)

        node_path = research_node.get_path()
        if not node_path:
            return [manager]

        # Load artifacts from the artifacts directory
        artifacts_dir = node_path / "Artifacts"
        if artifacts_dir.exists():
            for artifact_file in artifacts_dir.iterdir():
                if artifact_file.is_file() and artifact_file.suffix == ".md":
                    try:
                        artifact = Artifact.load_from_file(artifact_file)
                        manager.artifacts.append(artifact)
                    except Exception as e:
                        print(f"Error loading artifact {artifact_file}: {e}")

        return [manager]

    def add_artifact(self, artifact):
        if artifact.name in (a.name for a in self.artifacts):
            raise ValueError("One node can't have multiple artifacts with same name, please check the commands.")
        self.artifacts.append(artifact)
        self.save()

    def save(self):
        """Save artifacts to disk"""
        node_path = self.node.get_path()
        if not node_path:
            return

        # Create artifacts directory
        artifacts_dir = node_path / "Artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        # Save each artifact
        for artifact in self.artifacts:
            artifact.save_to_file(artifacts_dir)
