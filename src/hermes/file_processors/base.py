from abc import ABC, abstractmethod
import os
from typing import Any

class FileProcessor(ABC):
    @abstractmethod
    def read_file(self, file_path: str) -> Any:
        pass
    
    def exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    @abstractmethod
    def write_file(self, file_path: str, content: str, mode: str = 'w') -> None:
        pass
