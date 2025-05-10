from pathlib import Path

from hermes.chat.interface.assistant.deep_research_assistant.engine.research.file_system.disk_file_system import DiskFileSystem
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_project_component.external_file import (
    ExternalFilesManager,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_project_component.knowledge_base import (
    KnowledgeBase,
    KnowledgeEntry,
)
from hermes.chat.interface.assistant.deep_research_assistant.engine.research.research_project_component.permanent_log import (
    NodePermanentLogs,
)

from . import Research, ResearchNode


class ResearchImpl(Research):
    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory
        self.file_system = DiskFileSystem()
        self.root_node = None
        self._permanent_logs = NodePermanentLogs()
        self._research_initiated = False

        # Create instances for knowledge base and external files
        self._knowledge_base = KnowledgeBase(self.file_system, self.root_directory / "_knowledge_base.md")
        self._external_files_manager = ExternalFilesManager(self.file_system, self.root_directory / "_ExternalFiles")

    def research_already_exists(self) -> bool:
        """Check if research data already exists in the root directory"""
        # Look for the research metadata file
        metadata_path = self.root_directory / "research_metadata.json"
        return self.file_system.file_exists(metadata_path)

    def research_initiated(self) -> bool:
        """Return whether research has been initiated"""
        return self._research_initiated and self.root_node is not None

    def initiate_research(self, root_node: ResearchNode):
        """Initialize a new research project"""
        self.root_node = root_node
        # Set the root node path
        if isinstance(root_node, ResearchNode):
            root_node.set_path(self.root_directory)

        # Create the necessary directories
        self._create_directory_structure()

        # Save metadata about the research
        self._save_research_metadata()

        self._research_initiated = True

    def load_existing_research(self):
        """Load an existing research project"""
        # Load knowledge base and external files
        self._knowledge_base.load_entries()
        self._external_files_manager.load_external_files()

        self._research_initiated = True

    def get_root_node(self) -> ResearchNode:
        """Get the root node of the research"""
        if not self.research_initiated():
            raise ValueError("Research not initiated")
        return self.root_node

    def get_permanent_logs(self) -> NodePermanentLogs:
        """Get the permanent logs for the research"""
        return self._permanent_logs

    def add_knowledge_entry(self, entry: KnowledgeEntry) -> None:
        """Add a new entry to the knowledge base"""
        self._knowledge_base.add_entry(entry)

    def get_knowledge_base(self) -> list[KnowledgeEntry]:
        """Get all knowledge base entries"""
        return self._knowledge_base.get_entries()

    def add_external_file(self, name: str, content: str, summary: str = "") -> None:
        """Add an external file"""
        self._external_files_manager.add_external_file(name, content, summary)

    def get_external_files(self) -> dict:
        """Get all external files"""
        return self._external_files_manager.get_external_files()

    def _create_directory_structure(self):
        """Create the necessary directory structure for the research"""
        # Create the root directory if it doesn't exist
        if not self.file_system.directory_exists(self.root_directory):
            self.file_system.create_directory(self.root_directory)

        # Create other necessary directories
        artifacts_dir = self.root_directory / "artifacts"
        self.file_system.create_directory(artifacts_dir)

        logs_dir = self.root_directory / "logs"
        self.file_system.create_directory(logs_dir)

        # Create external files directory
        external_files_dir = self.root_directory / "_ExternalFiles"
        self.file_system.create_directory(external_files_dir)

    def _save_research_metadata(self):
        """Save metadata about the research project"""
        import json
        from datetime import datetime

        metadata_path = self.root_directory / "research_metadata.json"

        metadata = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "root_node_title": self.root_node.get_title() if self.root_node else None,
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
