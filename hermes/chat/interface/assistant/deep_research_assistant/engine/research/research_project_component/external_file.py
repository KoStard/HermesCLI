from pathlib import Path

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system import FileSystem
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.filename import Filename
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.frontmatter_manager import FrontmatterManager
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component.artifact import Artifact


class ExternalFilesManager:
    """Manages external files for a research project."""

    def __init__(self, file_system: FileSystem, external_files_dir: Path):
        self._file_system = file_system
        self._external_files_dir = external_files_dir
        self._external_files: dict[str, Artifact] = {}

    def load_external_files(self) -> None:
        """Load external files from disk."""
        self._external_files = {}  # Clear existing cache

        if not self._file_system.directory_exists(self._external_files_dir):
            self._file_system.create_directory(self._external_files_dir)
            return

        for file_path in self._file_system.list_files(self._external_files_dir):
            try:
                content = self._file_system.read_file(file_path)

                frontmatter_manager = FrontmatterManager()

                metadata, content = frontmatter_manager.extract_frontmatter(content)
                name = metadata.get("name", file_path.stem)
                summary = metadata.get("summary", "")

                artifact = Artifact(
                    name=name,
                    content=content,
                    short_summary=summary,
                    is_external=True
                )

                # Use filename as the key
                self._external_files[file_path.name] = artifact
            except Exception as e:
                print(f"Error loading external file {file_path.name}: {e}")

    def add_external_file(self, name: str, content: str, summary: str = "") -> None:
        """Add an external file."""
        frontmatter_manager = FrontmatterManager()

        # Create an artifact
        artifact = Artifact(
            name=name,
            content=content,
            short_summary=summary,
            is_external=True
        )

        # Sanitize filename
        filename_handler = Filename(name)
        filename = filename_handler.get_os_aware_path() + ".md"

        # Ensure directory exists
        self._file_system.create_directory(self._external_files_dir)

        # Add metadata and save
        file_content = frontmatter_manager.add_frontmatter(
            content,
            {"name": name, "summary": summary}
        )

        file_path = self._external_files_dir / filename
        self._file_system.write_file(file_path, file_content, True)

        # Update the cache
        self._external_files[filename] = artifact

    def get_external_files(self) -> dict[str, Artifact]:
        """Get all external files."""
        return self._external_files.copy()
