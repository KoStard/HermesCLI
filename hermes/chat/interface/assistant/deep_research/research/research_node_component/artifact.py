from pathlib import Path
from typing import TYPE_CHECKING

from hermes.chat.interface.assistant.deep_research.research.file_system.dual_directory_file_system import DualDirectoryFileSystem
from hermes.chat.interface.assistant.deep_research.research.file_system.markdown_file_with_metadata import (
    MarkdownFileWithMetadataImpl,
)

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode


class Artifact:
    def __init__(self, name: str, content: str, short_summary: str, is_external: bool = False, path: Path | None = None) -> None:
        self.name = name
        self._content = content
        self.short_summary = short_summary
        self.is_external = is_external
        self._path: Path | None = path

    @property
    def content(self):
        if not self._path or not self._path.exists():
            return self._content
        return self._get_content()

    def _get_content(self) -> str:
        assert self._path
        md_file = MarkdownFileWithMetadataImpl.load_from_file(self._path)
        return md_file.get_content()

    def set_directory(self, directory_path: Path):
        self._path = MarkdownFileWithMetadataImpl(self.name).get_path(directory_path)

    @staticmethod
    def load_from_file(file_path: Path) -> "Artifact":
        """Load an artifact from a file"""
        md_file = MarkdownFileWithMetadataImpl.load_from_file(file_path)

        # Use name from metadata if present, otherwise use filename
        name = md_file.get_metadata().get("name", file_path.stem)
        summary = md_file.get_metadata().get("summary", "")

        return Artifact(name=name, content=md_file.get_content(), short_summary=summary, is_external=False, path=file_path)

    def save(self) -> None:
        """Save an artifact to a file with metadata"""
        md_file = MarkdownFileWithMetadataImpl(self.name, self._content)
        md_file.add_property("summary", self.short_summary)

        # Add is_external to metadata if true
        if self.is_external:
            md_file.add_property("is_external", True)

        assert self._path
        md_file.save_file_in_path(self._path)

    def __str__(self) -> str:
        """String representation of the artifact"""
        return f"{self.name}: {self.short_summary}"


class ArtifactManager:
    """Manages artifacts for a research node"""

    def __init__(self, node: "ResearchNode", dual_directory_fs: "DualDirectoryFileSystem"):
        self._node = node
        self._artifacts: list[Artifact] = []
        self._dual_directory_fs = dual_directory_fs

    @property
    def artifacts(self):
        return self._artifacts

    @classmethod
    def load_for_research_node(cls, research_node: "ResearchNode", dual_directory_fs: "DualDirectoryFileSystem") -> list["ArtifactManager"]:
        """Load artifacts for a research node"""
        artifacts_manager = cls(research_node, dual_directory_fs)

        node_path = research_node.get_path()
        if not node_path:
            return [artifacts_manager]

        artifacts_dir = dual_directory_fs.get_artifact_directory_for_node_path(node_path)
        artifacts_manager._load_artifacts_from_directory(artifacts_dir)

        return [artifacts_manager]

    def _load_artifacts_from_directory(self, artifacts_dir: Path) -> None:
        """Load all artifacts from a directory into the artifacts manager"""
        if not artifacts_dir.exists():
            return

        for artifact_file in artifacts_dir.iterdir():
            self._try_load_artifact_file(artifact_file)

    def _try_load_artifact_file(self, artifact_file: Path) -> None:
        """Attempt to load a single artifact file and add it to the manager"""
        if not artifact_file.is_file() or artifact_file.suffix != ".md":
            return

        try:
            artifact = Artifact.load_from_file(artifact_file)
            self._artifacts.append(artifact)
        except Exception as e:
            print(f"Error loading artifact {artifact_file}: {e}")

    def add_artifact(self, artifact: Artifact):
        if artifact.name in (a.name for a in self._artifacts):
            raise ValueError("One node can't have multiple artifacts with same name, please check the commands.")
        self._artifacts.append(artifact)
        directory = self._get_directory()
        assert directory
        artifact.set_directory(directory)
        artifact.save()

    def _get_directory(self) -> Path | None:
        node_path = self._node.get_path()
        if not node_path:
            return None

        return self._dual_directory_fs.get_artifact_directory_for_node_path(node_path)
