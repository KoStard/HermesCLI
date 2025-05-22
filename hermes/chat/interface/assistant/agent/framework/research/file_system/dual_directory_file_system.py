from pathlib import Path

from . import FileSystem
from .disk_file_system import DiskFileSystem


class DualDirectoryFileSystem(FileSystem):
    """
    File system that separates artifacts (Results/) from research data (Research/).

    - Results/: Contains all artifacts organized by subproblem hierarchy
    - Research/: Contains all internal research data (problem definitions, logs, etc.)
    """

    def __init__(self, root_directory: Path):
        self.root_directory = root_directory
        self.results_directory = root_directory / "Results"
        self.research_directory = root_directory / "Research"
        self._disk_fs = DiskFileSystem()

        # Ensure both directories exist
        self.create_directory(self.results_directory)
        self.create_directory(self.research_directory)

    def get_results_path(self, relative_path: Path = Path()) -> Path:
        """Get the absolute path in the Results directory"""
        return self.results_directory / relative_path

    def get_research_path(self, relative_path: Path = Path()) -> Path:
        """Get the absolute path in the Research directory"""
        return self.research_directory / relative_path

    def get_artifact_directory_for_node_path(self, node_path: Path) -> Path:
        """
        Get the Results directory path for artifacts from a given research node path.

        Args:
            node_path: Path to the research node (in Research/ directory)

        Returns:
            Corresponding path in Results/ directory where artifacts should be stored
        """
        # Convert research path to relative path from research directory
        relative_path = node_path.relative_to(self.research_directory)
        return self.results_directory / relative_path

    def get_node_path_from_artifact_directory(self, artifact_path: Path) -> Path:
        """
        Get the Research directory path for a node from its artifact directory path.

        Args:
            artifact_path: Path in the Results/ directory

        Returns:
            Corresponding path in Research/ directory
        """
        relative_path = artifact_path.relative_to(self.results_directory)
        return self.research_directory / relative_path

    # Delegate core file system operations to disk file system
    def read_file(self, path: Path) -> str:
        return self._disk_fs.read_file(path)

    def write_file(self, path: Path, content: str, auto_create_directories: bool = True) -> None:
        return self._disk_fs.write_file(path, content, auto_create_directories)

    def copy_file(self, origin_path: Path, destination_path: Path) -> None:
        return self._disk_fs.copy_file(origin_path, destination_path)

    def directory_exists(self, path: Path) -> bool:
        return self._disk_fs.directory_exists(path)

    def file_exists(self, path: Path) -> bool:
        return self._disk_fs.file_exists(path)

    def create_directory(self, path: Path) -> None:
        return self._disk_fs.create_directory(path)

    def list_files(self, directory: Path, pattern: str | None = None) -> list[Path]:
        return self._disk_fs.list_files(directory, pattern)

    def is_empty(self, directory: Path) -> bool:
        return self._disk_fs.is_empty(directory)

    def list_artifacts_recursive(self, node_relative_path: Path = Path()) -> list[Path]:
        """
        List all artifact files recursively from the Results directory.

        Args:
            node_relative_path: Relative path from the root (empty for root artifacts)

        Returns:
            List of paths to all .md files in the Results directory tree
        """
        results_path = self.get_results_path(node_relative_path)
        if not self.directory_exists(results_path):
            return []

        artifacts = []
        for path in results_path.rglob("*.md"):
            if path.is_file():
                artifacts.append(path)

        return artifacts
