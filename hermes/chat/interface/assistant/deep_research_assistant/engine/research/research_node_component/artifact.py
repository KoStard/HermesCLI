from dataclasses import dataclass
from pathlib import Path
from typing import List

from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.frontmatter_manager import FrontmatterManager
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_node_component import ResearchNodeComponent


@dataclass
class Artifact:
    name: str
    content: str
    short_summary: str
    is_external: bool = False

    @staticmethod
    def load_from_file(file_path: Path) -> "Artifact":
        """Load an artifact from a file"""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        
        frontmatter_manager = FrontmatterManager()
        metadata, content = frontmatter_manager.extract_frontmatter(content)
        
        # Use name from metadata if present, otherwise use derived name
        name = metadata.get("name", file_path.stem)
        summary = metadata.get("summary", "")
        
        return Artifact(
            name=name, 
            content=content, 
            short_summary=summary
        )

    def save_to_file(self, file_path: Path) -> None:
        """Save an artifact to a file with metadata"""
        frontmatter_manager = FrontmatterManager()
        
        metadata = {
            "name": self.name,
            "summary": self.short_summary
        }
        
        content = frontmatter_manager.add_frontmatter(self.content, metadata)
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)


class ArtifactManager(ResearchNodeComponent):
    """Manages artifacts for a research node"""
    
    def __init__(self, node: ResearchNode):
        self.node = node
        self.artifacts: List[Artifact] = []
    
    @classmethod
    def load_for_research_node(cls, research_node: ResearchNode) -> List["ArtifactManager"]:
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
            filename = f"{artifact.name}.md"
            artifact.save_to_file(artifacts_dir / filename)
