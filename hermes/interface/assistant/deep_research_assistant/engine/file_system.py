import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

from hermes.interface.assistant.deep_research_assistant.engine.frontmatter_manager import FrontmatterManager


@dataclass
class Artifact:
    name: str
    content: str
    is_fully_visible: bool = False  # Default to half-closed (not fully visible)

    frontmatter_manager = FrontmatterManager()

    @staticmethod
    def load_from_file(file_path: Path) -> "Artifact":
        with open(file_path, "r") as f:
            content = f.read()
        metadata, content = FrontmatterManager().extract_frontmatter(content)
        name = metadata.get("name", file_path.name.rsplit('.', 1)[0])
        return Artifact(name=name, content=content, is_fully_visible=False)

    def save_to_file(self, file_path: Path) -> None:
        content = self.frontmatter_manager.add_frontmatter(self.content, {"name": self.name})
        with open(file_path, "w") as f:
            f.write(content)


class ProblemStatus(Enum):
    NOT_STARTED = "NOT_STARTED"  # Problem has not been started yet
    PENDING = "PENDING"  # Problem is temporarily paused (focus moved to child)
    CURRENT = "CURRENT"  # Problem is currently being worked on
    FINISHED = "FINISHED"  # Problem has been successfully completed
    FAILED = "FAILED"  # Problem could not be solved
    CANCELLED = "CANCELLED"  # Problem was determined to be unnecessary


@dataclass
class Node:
    title: str
    problem_definition: str
    criteria: List[str] = field(default_factory=list)
    criteria_done: List[bool] = field(default_factory=list)
    artifacts: Dict[str, Artifact] = field(default_factory=dict)
    subproblems: Dict[str, "Node"] = field(default_factory=dict)
    parent: Optional["Node"] = None
    path: Optional[Path] = None
    status: ProblemStatus = ProblemStatus.NOT_STARTED
    depth_from_root: int = 0

    def add_criteria(self, criteria: str) -> int:
        """Add criteria and return its index"""
        # Check if criteria already exists
        if criteria in self.criteria:
            return self.criteria.index(criteria)

        self.criteria.append(criteria)
        self.criteria_done.append(False)
        return len(self.criteria) - 1

    def mark_criteria_as_done(self, index: int) -> bool:
        """Mark criteria as done and return success"""
        if 0 <= index < len(self.criteria):
            self.criteria_done[index] = True
            return True
        return False

    def add_subproblem(self, title: str, content: str) -> "Node":
        """Add a subproblem and return it"""
        # Check if subproblem already exists
        if title in self.subproblems:
            return self.subproblems[title]

        subproblem = Node(
            title=title, 
            problem_definition=content, 
            parent=self,
            depth_from_root=self.depth_from_root + 1
        )
        self.subproblems[title] = subproblem
        return subproblem

    def add_artifact(self, name: str, content: str) -> None:
        """Add an artifact"""
        self.artifacts[name] = Artifact(
            name=name, content=content, is_fully_visible=False
        )

    def append_to_problem_definition(self, content: str) -> None:
        """Append to the problem definition"""
        self.problem_definition += "\n\n" + content

    def get_criteria_met_count(self) -> int:
        """Get the number of criteria met"""
        return sum(self.criteria_done)

    def get_criteria_total_count(self) -> int:
        """Get the total number of criteria"""
        return len(self.criteria)

    def get_criteria_status(self) -> str:
        """Get a string representation of criteria status"""
        met = self.get_criteria_met_count()
        total = self.get_criteria_total_count()
        return f"[{met}/{total} criteria met]"

    def get_status_emoji(self) -> str:
        """Get an emoji representation of the problem status"""
        status_emojis = {
            ProblemStatus.NOT_STARTED: "🆕",
            ProblemStatus.PENDING: "⏳",
            ProblemStatus.CURRENT: "🔍",
            ProblemStatus.FINISHED: "✅",
            ProblemStatus.FAILED: "❌",
            ProblemStatus.CANCELLED: "🚫",
        }
        return status_emojis.get(self.status, "🆕")

    def get_status_label(self) -> str:
        """Get a short label for the problem status"""
        return self.status.value


class FileSystem:
    def __init__(self, root_dir: str = "research"):
        self.root_dir = Path(root_dir)
        self.root_node: Optional[Node] = None
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.frontmatter_manager = FrontmatterManager()

        # Ensure the root directory exists
        os.makedirs(self.root_dir, exist_ok=True)

    def create_root_problem(self, title: str, content: str) -> Node:
        """Create the root problem"""
        # Create root directory if it doesn't exist
        self.root_dir.mkdir(parents=True, exist_ok=True)

        # Create node and set its path
        self.root_node = Node(title=title, problem_definition=content, path=self.root_dir, depth_from_root=0)

        # Create all necessary directories
        self._create_node_directories(self.root_node)

        # Write files to disk
        self._write_node_to_disk(self.root_node)

        return self.root_node

    def load_existing_problem(self) -> Optional[Node]:
        """Check if a problem already exists and load it"""
        self.root_node = self._recursively_load_problems(self.root_dir, parent_node=None)
        return self.root_node

    def _recursively_load_problems(self, node_dir: Path, parent_node: Optional[Node]) -> Optional[Node]:
        if not node_dir.exists():
            return None

        # Check if problem definition file exists
        problem_def_file = node_dir / "Problem Definition.md"
        if not problem_def_file.exists():
            return None

        # Read problem definition and extract front-matter
        title, problem_definition = self._read_problem_definition_with_frontmatter(
            problem_def_file
        )

        # If no title in front-matter, use directory name as fallback
        if not title:
            title = node_dir.name

        # Create root node
        node = Node(title=title,
                    problem_definition=problem_definition,
                    path=node_dir,
                    parent=parent_node,
                    depth_from_root=parent_node.depth_from_root + 1 if parent_node else 0)

        if parent_node:
            parent_node.subproblems[title] = node

        # Load criteria if they exist
        criteria_file = node_dir / "Criteria of Definition of Done.md"
        criteria, criteria_done = self._read_criteria_file(criteria_file)
        node.criteria.extend(criteria)
        node.criteria_done.extend(criteria_done)

        # Load artifacts
        artifacts_dir = node_dir / "Artifacts"
        node.artifacts.update(self._read_artifacts(artifacts_dir))

        subproblems_dir = node.path / "Subproblems"
        if subproblems_dir.exists():
            for subproblem_dir in subproblems_dir.iterdir():
                self._recursively_load_problems(subproblem_dir, node)

        return node

    def _read_artifacts(self, artifacts_dir: Path) -> Dict[str, Artifact]:
        """Read artifacts from the artifacts directory"""
        artifacts = {}
        if artifacts_dir.exists():
            for artifact_file in artifacts_dir.iterdir():
                if artifact_file.is_file():
                    artifact = Artifact.load_from_file(artifact_file)
                    artifacts[artifact_file.name] = artifact
        return artifacts

    def get_parent_chain(self, node: Node) -> List[Node]:
        """Get the parent chain including the given node"""
        chain = []
        current = node
        while current:
            chain.append(current)
            current = current.parent
        return list(reversed(chain))

    def get_problem_hierarchy(self, current_node: Optional[Node] = None) -> str:
        """Get the problem hierarchy as a string"""
        if not self.root_node:
            return ""

        result = []
        
        # Build the hierarchy tree recursively starting from root
        self._build_hierarchy_tree(self.root_node, result, 0, current_node)
        
        return "\n".join(result)
        
    def _build_hierarchy_tree(self, node: Node, result: List[str], indent_level: int, current_node: Optional[Node] = None) -> None:
        """
        Recursively build the hierarchy tree in XML-like format
        
        Args:
            node: The current node to process
            result: List to append formatted strings to
            indent_level: Current indentation level
            current_node: The currently active node to highlight
        """
        # Format node information
        artifacts_count = len(node.artifacts)
        criteria_met = node.get_criteria_met_count()
        criteria_total = node.get_criteria_total_count()
        node_status = node.status.value
        
        # Check if this is the current node
        is_current = node == current_node
        node_title = node.title
        
        # Create indentation
        indent = "  " * indent_level
        
        # Start tag with attributes
        opening_tag = f'{indent}<"{node_title}" '
        opening_tag += f'status="{node_status}" '
        opening_tag += f'criteriaProgress={criteria_met}/{criteria_total} '
        opening_tag += f'depth={node.depth_from_root} '
        opening_tag += f'artifacts={artifacts_count} '
        
        if is_current:
            opening_tag += 'isCurrent="true" '
            
        # Close the opening tag
        if not node.subproblems:
            # Self-closing tag if no children
            opening_tag += '/>'
            result.append(opening_tag)
        else:
            # Opening tag with children
            opening_tag += '>'
            result.append(opening_tag)
            
            # Process children with increased indentation
            for title, subproblem in node.subproblems.items():
                self._build_hierarchy_tree(subproblem, result, indent_level + 1, current_node)
                
            # Closing tag
            result.append(f'{indent}</{node_title}">')

    def update_files(self) -> None:
        """Update all files on disk"""
        with self.lock:
            if self.root_node:
                # First ensure all directories exist
                self._create_node_directories(self.root_node)
                # Then write all files
                self._write_node_to_disk(self.root_node)

    def _create_node_directories(self, node: Node) -> None:
        """Create all necessary directories for a node"""
        if not node.path:
            if node.parent and node.parent.path:
                # Create subproblem directory
                subproblems_dir = node.parent.path / "Subproblems"
                subproblems_dir.mkdir(exist_ok=True)

                # Create directory for this subproblem
                node_dir = subproblems_dir / self._sanitize_filename(node.title)
                node_dir.mkdir(exist_ok=True)

                node.path = node_dir
            else:
                # This shouldn't happen, but just in case
                return

        # Create artifacts directory
        artifacts_dir = node.path / "Artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        # Create subproblems directory
        subproblems_dir = node.path / "Subproblems"
        subproblems_dir.mkdir(exist_ok=True)

        # Create logs_and_debug directory
        logs_dir = node.path / "logs_and_debug"
        logs_dir.mkdir(exist_ok=True)

        # Recursively create directories for subproblems
        for subproblem in node.subproblems.values():
            self._create_node_directories(subproblem)

    def _write_node_to_disk(self, node: Node) -> None:
        """Write a node to disk"""
        if not node.path:
            self._create_node_directories(node)

        # Write problem definition with front-matter
        with open(node.path / "Problem Definition.md", "w") as f:
            content = self.frontmatter_manager.add_frontmatter(node.problem_definition, {
                "title": node.title
            })
            f.write(content)

        # Write criteria (always create the file)
        with open(node.path / "Criteria of Definition of Done.md", "w") as f:
            if node.criteria:
                for i, (criterion, done) in enumerate(
                    zip(node.criteria, node.criteria_done)
                ):
                    status = "[x]" if done else "[ ]"
                    f.write(f"{i+1}. {status} {criterion}\n")

        # Write breakdown structure (always create the file)
        with open(node.path / "Breakdown Structure.md", "w") as f:
            if node.subproblems:
                for title, subproblem in node.subproblems.items():
                    f.write(f"## {title}\n\n")
                    f.write(f"{subproblem.problem_definition}\n\n")

        # Write artifacts
        for name, artifact in node.artifacts.items():
            filename = self._sanitize_filename(name)
            # Add .md extension if no extension exists
            if "." not in filename:
                filename = filename + ".md"
            artifact.save_to_file(node.path / "Artifacts" / filename)

        # Recursively write subproblems
        for subproblem in node.subproblems.values():
            self._write_node_to_disk(subproblem)

    def _read_problem_definition_with_frontmatter(
        self, file_path: Path
    ) -> Tuple[Optional[str], str]:
        """
        Read a problem definition file and extract front-matter metadata

        Returns:
            Tuple[Optional[str], str]: (title, problem_definition)
        """
        if not file_path.exists():
            return None, ""

        with open(file_path, "r") as f:
            full_content = f.read()

        metadata, content = self.frontmatter_manager.extract_frontmatter(full_content)
        return metadata.get('title'), content

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename to be valid on the filesystem"""
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        # Ensure the filename isn't too long
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename

    def _read_criteria_file(self, criteria_file: Path):
        criteria = []
        criteria_done = []
        if criteria_file.exists():
            with open(criteria_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and line[0].isdigit():
                        # Parse criteria line (format: "1. [x] Criterion text")
                        parts = line.split(". ", 1)
                        if len(parts) == 2:
                            criterion_text = parts[1]
                            # Check if it's marked as done
                            done = "[x]" in criterion_text or "[X]" in criterion_text
                            # Remove status marker
                            criterion_text = (
                                criterion_text.split("] ", 1)[1]
                                if "] " in criterion_text
                                else criterion_text
                            )
                            criteria.append(criterion_text)
                            criteria_done.append(done)
        return criteria, criteria_done

    def is_node_too_deep(self, node: Node, max_depth: int = 3) -> bool:
        """Check if a node is too deep in the hierarchy"""
        return node.depth_from_root > max_depth

    def get_all_nodes(self):
        root_node = self.root_node
        if not root_node:
            return []

        all_nodes = self.get_all_nodes_recursive(root_node)
        return all_nodes

    def get_all_nodes_recursive(self, node: Node):
        all_nodes = [node]
        for subproblem in node.subproblems.values():
            all_nodes.extend(self.get_all_nodes_recursive(subproblem))
        return all_nodes
