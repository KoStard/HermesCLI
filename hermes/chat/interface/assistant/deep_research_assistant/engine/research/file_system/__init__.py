from abc import ABC, abstractmethod
from pathlib import Path

# Handle all file system access, I think this abstraction will benefit me in long run


class FileSystem(ABC):
    @abstractmethod
    def read_file(self, path: Path) -> str:
        pass

    @abstractmethod
    def write_file(self, path: Path, content: str, auto_create_directories: bool):
        pass

    @staticmethod
    def get_path(raw_path: str) -> Path:
        return Path(raw_path).expanduser()

    @abstractmethod
    def copy_file(self, origin_path: Path, destination_path: Path):
        pass

    @abstractmethod
    def directory_exists(self, path: Path) -> bool:
        pass

    @abstractmethod
    def file_exists(self, path: Path) -> bool:
        pass

    @abstractmethod
    def create_directory(self, path: Path) -> None:
        pass

    @abstractmethod
    def list_files(self, directory: Path, pattern: str | None = None) -> list[Path]:
        pass
