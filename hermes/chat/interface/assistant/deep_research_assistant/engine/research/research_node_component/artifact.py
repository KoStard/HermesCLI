from dataclasses import dataclass
from pathlib import Path
from typing import List

from hermes.chat.interface.assistant.deep_research_assistant.engine.research import ResearchNode
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.markdown_file_with_metadata import MarkdownFileWithMetadataImpl
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
        md_file = MarkdownFileWithMetadataImpl.load_from_file(str(file_path))
        
        # Use name from metadata if present, otherwise use filename
        name = md_file.get_metadata().get("name", file_path.stem)
        summary = md_file.get_metadata().get("summary", "")
        
        return Artifact(
            name=name, 
            content=md_file.get_content(),
            short_summary=summary
        )

    def save_to_file(self, file_path: Path) -> None:
        """Save an artifact to a file with metadata"""
        md_file = MarkdownFileWithMetadataImpl(self.name, self.content)
        md_file.add_property("name", self.name)
        md_file.add_property("summary", self.short_summary)
        
        # MarkdownFileWithMetadataImpl.save_file handles directory creation
        md_file.save_file(str(file_path))


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
