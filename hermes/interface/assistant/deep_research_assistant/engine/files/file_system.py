import hashlib
import json
import os
import re
import threading
import yaml
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .frontmatter_manager import FrontmatterManager
from .knowledge_entry import KnowledgeEntry

# Define a unique separator for knowledge base entries in the Markdown file
_KNOWLEDGE_SEPARATOR = "\n\n<!-- HERMES_KNOWLEDGE_ENTRY_SEPARATOR -->\n\n"


@dataclass
class Artifact:
    name: str
    content: str
    is_external: bool = False
    
    frontmatter_manager = FrontmatterManager()

    @staticmethod
    def load_from_file(file_path: Path) -> "Artifact":
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        metadata, content = FrontmatterManager().extract_frontmatter(content)
        # Derive name from filename without extension
        name = file_path.stem
        # Use name from metadata if present, otherwise use derived name
        name = metadata.get("name", name)
        return Artifact(name=name, content=content)

    def save_to_file(self, file_path: Path) -> None:
        content = self.frontmatter_manager.add_frontmatter(
            self.content, {"name": self.name}
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)


class ProblemStatus(Enum):
    NOT_STARTED = "NOT_STARTED"  # Problem has not been started yet
    PENDING = "PENDING"  # Problem is temporarily paused (focus moved to child)
    IN_PROGRESS = "IN_PROGRESS"  # Problem is currently being worked on
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
    visible_artifacts: Dict[str, bool] = field(default_factory=dict)  # Track visibility state for all artifacts

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
            depth_from_root=self.depth_from_root + 1,
        )
        self.subproblems[title] = subproblem
        return subproblem

    def add_artifact(self, name: str, content: str) -> None:
        """Add an artifact"""
        self.artifacts[name] = Artifact(
            name=name, content=content
        )

    def append_to_problem_definition(self, content: str) -> None:
        """Append to the problem definition"""
        self.problem_definition += "\n\nUPDATE\n" + content

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
            ProblemStatus.IN_PROGRESS: "🔍",
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
        self.root_dir = Path(root_dir).resolve()
        self.root_node: Optional[Node] = None
        self._external_files: Dict[str, Artifact] = {}
        self.knowledge_base: List[KnowledgeEntry] = []
        self.lock = threading.RLock()
        self.frontmatter_manager = FrontmatterManager()

        # Ensure the root directory exists
        self.root_dir.mkdir(parents=True, exist_ok=True)

        # Create the external files directory
        self.external_files_dir = self.root_dir / "_ExternalFiles" # Prefix with _ for clarity
        self.external_files_dir.mkdir(exist_ok=True)

        # Define path for the knowledge base file
        self._knowledge_base_file = self.root_dir / "_knowledge_base.md"

        # Load existing data
        self.load_external_files()
        self.load_knowledge_base()

    def create_root_problem(self, title: str, content: str) -> Node:
        """Create the root problem"""
        if self.root_node:
            # Avoid creating multiple root problems if one already exists in memory
            # Or handle merging/updating if necessary
            print(
                f"Warning: Root problem '{self.root_node.title}' already exists. Overwriting is not implemented."
            )
            return self.root_node
        # Create root directory if it doesn't exist
        self.root_dir.mkdir(parents=True, exist_ok=True)

        # Create node and set its path
        self.root_node = Node(
            title=title,
            problem_definition=content,
            path=self.root_dir,
            depth_from_root=0,
        )

        # Create all necessary directories
        self._create_node_directories(self.root_node)

        # Write files to disk
        self._write_node_to_disk(self.root_node)

        return self.root_node

    def load_existing_problem(self) -> Optional[Node]:
        """Check if a problem already exists and load it"""
        # External files are loaded during __init__
        self.root_node = self._recursively_load_problems(
            self.root_dir, parent_node=None
        )
        return self.root_node

    def _recursively_load_problems(
        self, node_dir: Path, parent_node: Optional[Node]
    ) -> Optional[Node]:
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
        node = Node(
            title=title,
            problem_definition=problem_definition,
            path=node_dir,
            parent=parent_node,
            depth_from_root=parent_node.depth_from_root + 1 if parent_node else 0,
        )

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
                if artifact_file.is_file() and artifact_file.suffix == ".md":
                    artifact = Artifact.load_from_file(artifact_file)
                    # Use artifact's name (derived from filename or metadata) as the key
                    artifacts[artifact.name] = artifact
        return artifacts

    def add_external_file(self, name: str, content: str) -> None:
        """Add an external file to the file system"""
        # Create an artifact for the external file
        artifact = Artifact(name=name, content=content)

        # If root node exists, add to its external_files
        if self.root_node:
            self.root_node.external_files[name] = artifact
        # Always write to disk with .md extension
        filename = self._sanitize_filename(name) + ".md"

        # Ensure the external files directory exists (should be redundant due to __init__)
        self.external_files_dir.mkdir(exist_ok=True)

        file_path = self.external_files_dir / filename
        try:
            # Use Artifact's save method which includes frontmatter
            artifact.save_to_file(file_path)
            # Update the central dictionary
            self._external_files[filename] = artifact
        except Exception as e:
            print(f"Error saving external file {filename}: {e}")

    def load_external_files(self) -> None:
        """Load external files from disk into the central dictionary"""
        self._external_files = {}  # Clear existing cache before loading

        if self.external_files_dir.exists():
            for file_path in self.external_files_dir.iterdir():
                if file_path.is_file():
                    try:
                        artifact = Artifact.load_from_file(file_path)
                        artifact.is_fully_visible = (
                            True  # External files should be fully visible
                        )
                        self._external_files[file_path.name] = artifact
                    except Exception as e:
                        print(f"Error loading external file {file_path.name}: {e}")

    def get_external_files(self) -> Dict[str, Artifact]:
        """Get the dictionary of loaded external files"""
        # Consider adding a check here to reload if needed, but __init__ load should suffice for now
        # Return a copy to prevent external modification
        with self.lock:
            return self._external_files.copy()

    def load_knowledge_base(self) -> None:
        """Load knowledge base entries from the Markdown file."""
        with self.lock:
            self.knowledge_base = []
            if not self._knowledge_base_file.exists():
                return  # No file, start with empty list

            try:
                full_content = self._knowledge_base_file.read_text(encoding="utf-8")
                # Split entries using the defined separator
                entry_blocks = full_content.split(_KNOWLEDGE_SEPARATOR)

                for block in entry_blocks:
                    block = block.strip()
                    if not block:
                        continue
                    try:
                        metadata, content = self.frontmatter_manager.extract_frontmatter(block)
                        if metadata: # Ensure metadata was found
                            entry = KnowledgeEntry.from_dict(metadata, content)
                            self.knowledge_base.append(entry)
                        else:
                            print(f"Warning: Could not parse frontmatter for a knowledge block in {self._knowledge_base_file}")
                    except Exception as e_parse:
                        print(f"Warning: Error parsing knowledge entry block: {e_parse}\nBlock content:\n{block[:200]}...")

            except FileNotFoundError:
                pass # Expected if file doesn't exist yet
            except Exception as e_read:
                print(f"Error loading knowledge base file {self._knowledge_base_file}: {e_read}")
                # Decide on recovery strategy: potentially backup old file, start fresh?
                # For now, we start with an empty list if loading fails.
                self.knowledge_base = []

    def save_knowledge_base(self) -> None:
        """Save the current knowledge base entries to the Markdown file."""
        with self.lock:
            try:
                entry_strings = []
                # Sort by timestamp before saving (optional, but keeps file consistent)
                sorted_entries = sorted(self.knowledge_base, key=lambda x: x.timestamp)
                for entry in sorted_entries:
                    metadata = entry.to_dict()
                    entry_string = self.frontmatter_manager.add_frontmatter(entry.content, metadata)
                    entry_strings.append(entry_string)

                # Join entries with the separator
                full_content = _KNOWLEDGE_SEPARATOR.join(entry_strings)
                self._knowledge_base_file.write_text(full_content, encoding="utf-8")

            except Exception as e:
                print(f"Error saving knowledge base file {self._knowledge_base_file}: {e}")

    def add_knowledge_entry(self, entry: KnowledgeEntry) -> None:
        """Add a new entry to the knowledge base and save immediately."""
        with self.lock:
            self.knowledge_base.append(entry)
            # Save immediately to ensure persistence
            self.save_knowledge_base()

    def get_knowledge_base(self) -> List[KnowledgeEntry]:
        """Get a copy of the current knowledge base entries."""
        with self.lock:
            # Return a copy to prevent external modification
            return self.knowledge_base[:]

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

    def _build_hierarchy_tree(
        self,
        node: Node,
        result: List[str],
        indent_level: int,
        current_node: Optional[Node] = None,
    ) -> None:
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
        opening_tag += f"criteriaProgress={criteria_met}/{criteria_total} "
        opening_tag += f"depth={node.depth_from_root} "
        opening_tag += f"artifacts={artifacts_count} "

        if is_current:
            opening_tag += 'isCurrent="true" '

        # Close the opening tag
        if not node.subproblems:
            # Self-closing tag if no children
            opening_tag += "/>"
            result.append(opening_tag)
        else:
            # Opening tag with children
            opening_tag += ">"
            result.append(opening_tag)

            # Process children with increased indentation
            for title, subproblem in node.subproblems.items():
                self._build_hierarchy_tree(
                    subproblem, result, indent_level + 1, current_node
                )

            # Closing tag
            result.append(f'{indent}</"{node_title}">')

    def update_files(self) -> None:
        """Update all files on disk"""
        with self.lock:
            if self.root_node:
                # First ensure all directories exist
                self._create_node_directories(self.root_node)
                # Then write all node-specific files
                self._write_node_to_disk(self.root_node)
                # Note: Knowledge base is saved separately by add_knowledge_entry

    def _create_node_directories(self, node: Node) -> None:
        """Create all necessary directories for a node"""
        if not node.path:
            if node.parent and node.parent.path:
                # Create subproblem directory
                subproblems_dir = node.parent.path / "Subproblems"
                subproblems_dir.mkdir(exist_ok=True)

                # Create directory for this subproblem using the sanitized title
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
        with open(node.path / "Problem Definition.md", "w", encoding="utf-8") as f:
            content = self.frontmatter_manager.add_frontmatter(
                node.problem_definition, {"title": node.title}
            )
            f.write(content)

        # Write criteria (always create the file)
        with open(node.path / "Criteria of Definition of Done.md", "w", encoding="utf-8") as f:
            if node.criteria:
                for i, (criterion, done) in enumerate(
                    zip(node.criteria, node.criteria_done)
                ):
                    status = "[x]" if done else "[ ]"
                    f.write(f"{i+1}. {status} {criterion}\n")

        # Write breakdown structure (always create the file)
        with open(node.path / "Breakdown Structure.md", "w", encoding="utf-8") as f:
            if node.subproblems:
                for title, subproblem in node.subproblems.items():
                    f.write(f"## {title}\n\n")
                    f.write(f"{subproblem.problem_definition}\n\n")

        # Write artifacts
        for name, artifact in node.artifacts.items():
            # Always save with .md extension
            filename = self._sanitize_filename(name) + ".md"
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

        with open(file_path, "r", encoding="utf-8") as f:
            full_content = f.read()

        metadata, content = self.frontmatter_manager.extract_frontmatter(full_content)
        return metadata.get("title"), content

    def _sanitize_filename(self, original_filename: str) -> str:
        """
        Sanitizes a filename or directory name component to be safe for the filesystem,
        significantly shorter to avoid MAX_PATH issues, and reasonably unique.

        - Replaces invalid characters.
        - Removes leading/trailing whitespace and periods.
        - Replaces multiple consecutive underscores with a single one.
        - Truncates the base name to a fixed length.
        - Appends a short hash of the original name for uniqueness.
        - Preserves the original file extension.
        """
        _MAX_COMPONENT_BASE_LENGTH = 50 # Max length for the base name part (excluding hash and extension)
        _HASH_LENGTH = 8 # Length of the hash suffix

        original_filename = original_filename.strip()
        if not original_filename:
            # Return a default name with a hash of something unique if possible,
            # or a fixed string if not. Using a fixed string for simplicity here.
            return "_empty_" + hashlib.sha1(os.urandom(16)).hexdigest()[:_HASH_LENGTH]

        # Separate base name and extension
        base_name, extension = os.path.splitext(original_filename)
        extension = extension.lower() # Normalize extension

        # Generate hash from the original full name (before any modification)
        hasher = hashlib.sha1(original_filename.encode('utf-8', 'ignore')) # Use ignore for robustness
        unique_suffix = hasher.hexdigest()[:_HASH_LENGTH]

        # Basic sanitization: replace invalid chars, collapse spaces/underscores
        sanitized_base = re.sub(r'[<>:"/\\|?*]+', '_', base_name) # Replace strictly invalid chars
        sanitized_base = re.sub(r'\s+', '_', sanitized_base) # Replace whitespace with underscore
        sanitized_base = re.sub(r'_+', '_', sanitized_base) # Collapse multiple underscores
        # Remove most non-alphanumeric characters, keeping underscores and hyphens
        sanitized_base = re.sub(r'[^a-zA-Z0-9_-]+', '', sanitized_base)
        # Remove leading/trailing underscores/hyphens/periods
        sanitized_base = re.sub(r'^[._-]+|[._-]+$', '', sanitized_base)

        # Handle cases where sanitization results in an empty string
        if not sanitized_base:
            sanitized_base = "sanitized" # Fallback name

        # Truncate the sanitized base name if it's too long
        if len(sanitized_base) > _MAX_COMPONENT_BASE_LENGTH:
            sanitized_base = sanitized_base[:_MAX_COMPONENT_BASE_LENGTH]
            # Ensure it doesn't end with an underscore/hyphen after truncation
            sanitized_base = sanitized_base.rstrip('_-')

        # Re-check for empty string after potential stripping
        if not sanitized_base:
            sanitized_base = "truncated" # Another fallback

        # Combine truncated base, hash suffix, and original extension
        # Format: {truncated_base}_{hash}{.extension}
        final_filename = f"{sanitized_base}_{unique_suffix}{extension}"

        # Final check on total length (less critical than component length, but good practice)
        # Windows max filename length is often 255 in practice for NTFS
        _MAX_FILENAME_LEN = 255
        if len(final_filename) > _MAX_FILENAME_LEN:
             # If even after truncation and hashing it's too long (very unlikely), truncate brutally
             # Keep the hash and extension if possible
             keep_len = _MAX_FILENAME_LEN - len(unique_suffix) - len(extension) -1 # -1 for the underscore
             if keep_len > 0:
                 final_filename = f"{sanitized_base[:keep_len]}_{unique_suffix}{extension}"
             else:
                 # Extremely unlikely: hash + extension is already too long. Just truncate the whole thing.
                 final_filename = final_filename[:_MAX_FILENAME_LEN]


        return final_filename

    def _read_criteria_file(self, criteria_file: Path):
        criteria = []
        criteria_done = []
        if criteria_file.exists():
            with open(criteria_file, "r", encoding="utf-8") as f:
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
