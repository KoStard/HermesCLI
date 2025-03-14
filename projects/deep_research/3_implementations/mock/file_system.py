import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Attachment:
    name: str
    content: str


@dataclass
class Node:
    title: str
    problem_definition: str
    criteria: List[str] = field(default_factory=list)
    criteria_done: List[bool] = field(default_factory=list)
    attachments: Dict[str, Attachment] = field(default_factory=dict)
    subproblems: Dict[str, 'Node'] = field(default_factory=dict)
    report: Optional[str] = None
    parent: Optional['Node'] = None
    path: Optional[Path] = None

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

    def add_subproblem(self, title: str, content: str) -> 'Node':
        """Add a subproblem and return it"""
        # Check if subproblem already exists
        if title in self.subproblems:
            return self.subproblems[title]
            
        subproblem = Node(title=title, problem_definition=content, parent=self)
        self.subproblems[title] = subproblem
        return subproblem

    def add_attachment(self, name: str, content: str) -> None:
        """Add an attachment"""
        self.attachments[name] = Attachment(name=name, content=content)

    def write_report(self, content: str) -> None:
        """Write a report"""
        self.report = content

    def append_to_problem_definition(self, content: str) -> None:
        """Append to the problem definition"""
        self.problem_definition += "\n\n" + content

    def get_criteria_met_count(self) -> int:
        """Get the number of criteria met"""
        return sum(self.criteria_done)

    def get_criteria_total_count(self) -> int:
        """Get the total number of criteria"""
        return len(self.criteria)


class FileSystem:
    def __init__(self, root_dir: str = "research"):
        self.root_dir = Path(root_dir)
        self.root_node: Optional[Node] = None
        self.current_node: Optional[Node] = None

    def create_root_problem(self, title: str, content: str) -> Node:
        """Create the root problem"""
        # Create root directory if it doesn't exist
        if not self.root_dir.exists():
            self.root_dir.mkdir(parents=True)
            
        # Create node and set its path
        self.root_node = Node(title=title, problem_definition=content)
        self.root_node.path = self.root_dir
        self.current_node = self.root_node
        
        # Create all necessary directories
        self._create_node_directories(self.root_node)
        
        # Write files to disk
        self._write_node_to_disk(self.root_node)
        
        return self.root_node

    def focus_down(self, title: str) -> Optional[Node]:
        """Focus on a subproblem"""
        if self.current_node and title in self.current_node.subproblems:
            self.current_node = self.current_node.subproblems[title]
            return self.current_node
        return None

    def focus_up(self) -> Optional[Node]:
        """Focus on the parent problem"""
        if self.current_node and self.current_node.parent:
            self.current_node = self.current_node.parent
            return self.current_node
        return None

    def get_parent_chain(self) -> List[Node]:
        """Get the parent chain"""
        chain = []
        node = self.current_node
        while node:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    def get_problem_hierarchy(self) -> str:
        """Get the problem hierarchy as a string"""
        if not self.root_node:
            return ""

        result = []
        
        # Add root
        result.append(f" └── Root: {self.root_node.title}")
        
        # Build the hierarchy
        current = self.current_node
        if current != self.root_node:
            path = []
            while current and current != self.root_node:
                path.append(current)
                current = current.parent
            
            path.reverse()
            
            for i, node in enumerate(path):
                parent = node.parent
                criteria_met = parent.get_criteria_met_count() if parent else 0
                criteria_total = parent.get_criteria_total_count() if parent else 0
                
                prefix = "     " * i + " └── "
                if i == len(path) - 1:
                    result.append(f"{prefix}CURRENT: {node.title}")
                else:
                    result.append(f"{prefix}Level {i+1}: {node.title} [{criteria_met}/{criteria_total} criteria met]")
        
        return "\n".join(result)
        
    def _create_node_directories(self, node: Node) -> None:
        """Create all necessary directories for a node"""
        if not node.path:
            if node.parent and node.parent.path:
                # Create subproblem directory
                subproblems_dir = node.parent.path / "Subproblems"
                if not subproblems_dir.exists():
                    subproblems_dir.mkdir(exist_ok=True)
                
                # Create directory for this subproblem
                node_dir = subproblems_dir / self._sanitize_filename(node.title)
                if not node_dir.exists():
                    node_dir.mkdir(exist_ok=True)
                
                node.path = node_dir
            else:
                # This shouldn't happen, but just in case
                return
        
        # Create attachments directory
        attachments_dir = node.path / "Attachments"
        if not attachments_dir.exists():
            attachments_dir.mkdir(exist_ok=True)
        
        # Create subproblems directory
        subproblems_dir = node.path / "Subproblems"
        if not subproblems_dir.exists():
            subproblems_dir.mkdir(exist_ok=True)
        
        # Recursively create directories for subproblems
        for subproblem in node.subproblems.values():
            self._create_node_directories(subproblem)

    def _write_node_to_disk(self, node: Node) -> None:
        """Write a node to disk"""
        if not node.path:
            self._create_node_directories(node)
        
        # Write problem definition
        with open(node.path / "Problem Definition.md", "w") as f:
            f.write(node.problem_definition)
        
        # Write criteria (always create the file)
        with open(node.path / "Criteria of Definition of Done.md", "w") as f:
            if node.criteria:
                for i, (criterion, done) in enumerate(zip(node.criteria, node.criteria_done)):
                    status = "[x]" if done else "[ ]"
                    f.write(f"{i+1}. {status} {criterion}\n")
        
        # Write report (always create the file)
        with open(node.path / "Report 3 Pager.md", "w") as f:
            if node.report:
                f.write(node.report)
        
        # Write breakdown structure (always create the file)
        with open(node.path / "Breakdown Structure.md", "w") as f:
            if node.subproblems:
                for title, subproblem in node.subproblems.items():
                    f.write(f"## {title}\n\n")
                    f.write(f"{subproblem.problem_definition}\n\n")
        
        # Write attachments
        for name, attachment in node.attachments.items():
            filename = self._sanitize_filename(name)
            with open(node.path / "Attachments" / filename, "w") as f:
                f.write(attachment.content)
        
        # Recursively write subproblems
        for subproblem in node.subproblems.values():
            self._write_node_to_disk(subproblem)
    
    def update_files(self) -> None:
        """Update all files on disk"""
        if self.root_node:
            # First ensure all directories exist
            self._create_node_directories(self.root_node)
            # Then write all files
            self._write_node_to_disk(self.root_node)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename to be valid on the filesystem"""
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Ensure the filename isn't too long
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
            
        return filename
