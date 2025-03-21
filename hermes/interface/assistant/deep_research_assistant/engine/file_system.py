import os
import threading
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


@dataclass
class Artifact:
    name: str
    content: str
    is_fully_visible: bool = False  # Default to half-closed (not fully visible)


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
        if not self.root_dir.exists():
            return None

        # Check if problem definition file exists
        problem_def_file = self.root_dir / "Problem Definition.md"
        if not problem_def_file.exists():
            return None

        # Read problem definition and extract front-matter
        title, problem_definition = self._read_problem_definition_with_frontmatter(
            problem_def_file
        )

        # If no title in front-matter, use directory name as fallback
        if not title:
            title = self.root_dir.name

        # Create root node
        self.root_node = Node(title=title, problem_definition=problem_definition, path=self.root_dir, depth_from_root=0)

        # Load criteria if they exist
        criteria_file = self.root_dir / "Criteria of Definition of Done.md"
        criteria, criteria_done = self._read_criteria_file(criteria_file)
        self.root_node.criteria.extend(criteria)
        self.root_node.criteria_done.extend(criteria_done)

        # Load artifacts
        artifacts_dir = self.root_dir / "Artifacts"
        self.root_node.artifacts.update(self._read_artifacts(artifacts_dir))

        # Load subproblems recursively
        self._load_subproblems(self.root_node)

        return self.root_node

    def _load_subproblems(self, parent_node: Node) -> None:
        """Recursively load subproblems for a node"""
        if not parent_node.path:
            return

        subproblems_dir = parent_node.path / "Subproblems"
        if not subproblems_dir.exists():
            return

        for subproblem_dir in subproblems_dir.iterdir():
            if not subproblem_dir.is_dir():
                continue

            # Load problem definition
            problem_def_file = subproblem_dir / "Problem Definition.md"
            if not problem_def_file.exists():
                continue

            # Read problem definition and extract front-matter
            title, problem_definition = self._read_problem_definition_with_frontmatter(
                problem_def_file
            )

            # If no title in front-matter, use directory name as fallback
            if not title:
                title = subproblem_dir.name
            subproblem = Node(
                title=title, 
                problem_definition=problem_definition, 
                parent=parent_node, 
                path=subproblem_dir,
                depth_from_root=parent_node.depth_from_root + 1
            )
            parent_node.subproblems[title] = subproblem

            # Load criteria
            criteria_file = subproblem_dir / "Criteria of Definition of Done.md"
            criteria, criteria_done = self._read_criteria_file(criteria_file)
            subproblem.criteria.extend(criteria)
            subproblem.criteria_done.extend(criteria_done)

            # Load artifacts
            artifacts_dir = subproblem_dir / "Artifacts"
            subproblem.artifacts.update(self._read_artifacts(artifacts_dir))

            # Recursively load subproblems
            self._load_subproblems(subproblem)

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
        self._build_hierarchy_tree(self.root_node, result, "", current_node)
        
        return "\n".join(result)
        
    def _build_hierarchy_tree(self, node: Node, result: List[str], prefix: str, current_node: Optional[Node] = None) -> None:
        """
        Recursively build the hierarchy tree
        
        Args:
            node: The current node to process
            result: List to append formatted strings to
            prefix: Prefix string for indentation
            current_node: The currently active node to highlight
        """
        # Format node information
        artifacts_count = len(node.artifacts)
        criteria_met = node.get_criteria_met_count()
        criteria_total = node.get_criteria_total_count()
        depth_indicator = f"[Depth: {node.depth_from_root}]"
        status_emoji = node.get_status_emoji()
        
        # Check if this is the current node
        is_current = node == current_node
        node_title = node.title
        
        # Format the node line
        if node == self.root_node:
            node_line = f"Root: {node_title}"
        else:
            node_line = node_title
            
        # Add status indicators
        if is_current:
            node_line = f"CURRENT: {node_line}"
            
        # Add metrics
        node_line = f"{status_emoji} {node_line} {depth_indicator} [{criteria_met}/{criteria_total} criteria met] [🗂️ {artifacts_count} artifacts]"
        
        # Add to result
        result.append(f"{prefix} └── {node_line}")
        
        # Process children with increased indentation
        child_prefix = prefix + "     "
        for title, subproblem in node.subproblems.items():
            self._build_hierarchy_tree(subproblem, result, child_prefix, current_node)

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
            # Add front-matter with title
            f.write("---\n")
            f.write(f"title: {node.title}\n")
            f.write("---\n\n")
            f.write(node.problem_definition)

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
            with open(node.path / "Artifacts" / filename, "w") as f:
                f.write(artifact.content)

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
            content = f.read()

        # Check for front-matter (between --- markers)
        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL
        )

        if frontmatter_match:
            # Extract front-matter and content
            frontmatter = frontmatter_match.group(1)
            problem_definition = frontmatter_match.group(2).strip()

            # Extract title from front-matter
            title_match = re.search(r"title:\s*(.*?)(\n|$)", frontmatter)
            title = title_match.group(1).strip() if title_match else None

            return title, problem_definition
        else:
            # No front-matter found, return the entire content as problem definition
            return None, content

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
        
    def _read_artifacts(self, artifacts_dir: Path):
        artifacts = {}
        if artifacts_dir.exists():
            for artifact_file in artifacts_dir.iterdir():
                if artifact_file.is_file():
                    with open(artifact_file, "r") as f:
                        # Load artifacts as half-closed by default
                        artifact_content = f.read()
                        artifact = Artifact(
                            name=artifact_file.name,
                            content=artifact_content,
                            is_fully_visible=False,
                        )
                        artifacts[artifact_file.name] = artifact
        return artifacts
