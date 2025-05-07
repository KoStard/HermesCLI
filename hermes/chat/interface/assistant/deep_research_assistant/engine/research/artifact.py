from dataclasses import dataclass
from pathlib import Path

from hermes.chat.interface.assistant.deep_research_assistant.engine.files.frontmatter_manager import FrontmatterManager


@dataclass
class Artifact:
    name: str
    content: str
    is_external: bool = False

    frontmatter_manager = FrontmatterManager()

    @staticmethod
    def load_from_file(file_path: Path) -> "Artifact":
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        metadata, content = FrontmatterManager().extract_frontmatter(content)
        # Derive name from filename without extension
        name = file_path.stem
        # Use name from metadata if present, otherwise use derived name
        name = metadata.get("name", name)
        return Artifact(name=name, content=content)

    def save_to_file(self, file_path: Path) -> None:
        content = self.frontmatter_manager.add_frontmatter(self.content, {"name": self.name})
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
