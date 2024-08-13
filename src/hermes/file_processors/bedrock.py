from .base import FileProcessor

class BedrockFileProcessor(FileProcessor):
    def read_file(self, file_path: str) -> bytes:
        if not self.exists(file_path):
            return b"empty"

        with open(file_path, 'rb') as file:
            return file.read()

    def write_file(self, file_path: str, content: str, mode: str = 'w') -> None:
        with open(file_path, mode, encoding='utf-8') as file:
            file.write(content)
