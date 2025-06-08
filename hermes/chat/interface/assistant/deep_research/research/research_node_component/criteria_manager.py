from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes.chat.interface.assistant.deep_research.research import ResearchNode


@dataclass
class Criterion:
    """A criterion for determining if a problem is done"""

    content: str
    is_completed: bool = False


class CriteriaManager:
    """Manages criteria for a research node"""

    def __init__(self, node: "ResearchNode"):
        self.node = node
        self.criteria: list[Criterion] = []

    @classmethod
    def _get_criteria_path(cls, node_path):
        """Get the path to the criteria file"""
        return node_path / "Criteria of Definition of Done.md"

    @classmethod
    def _parse_criterion_line(cls, line: str) -> tuple[str, bool] | None:
        """Parse a criterion line and return (content, is_completed) if valid"""
        line = line.strip()
        
        # Skip empty lines or non-criteria lines
        if not line or not line[0].isdigit():
            return None
            
        # Split into number and content
        parts = line.split(". ", 1)
        if len(parts) != 2:
            return None
            
        criterion_text = parts[1]
        
        # Check completion status
        done = "[x]" in criterion_text or "[X]" in criterion_text
        
        # Extract criterion content
        if "] " in criterion_text:
            criterion_text = criterion_text.split("] ", 1)[1]
            
        return criterion_text, done

    @classmethod
    def _read_criteria_from_file(cls, criteria_path, manager):
        """Read criteria from file and add them to the manager"""
        try:
            with open(criteria_path, encoding="utf-8") as f:
                for line in f:
                    result = cls._parse_criterion_line(line)
                    if result:
                        content, is_completed = result
                        manager.criteria.append(Criterion(content=content, is_completed=is_completed))
        except Exception as e:
            print(f"Error loading criteria: {e}")

    @classmethod
    def load_for_research_node(cls, research_node: "ResearchNode") -> list["CriteriaManager"]:
        """Load criteria for a research node"""
        manager = cls(research_node)

        node_path = research_node.get_path()
        if not node_path:
            return [manager]

        criteria_path = cls._get_criteria_path(node_path)
        if criteria_path.exists():
            cls._read_criteria_from_file(criteria_path, manager)

        return [manager]

    def save(self):
        """Save criteria to disk"""
        node_path = self.node.get_path()
        if not node_path:
            return

        # Save criteria
        criteria_path = node_path / "Criteria of Definition of Done.md"
        try:
            with open(criteria_path, "w", encoding="utf-8") as f:
                for i, criterion in enumerate(self.criteria):
                    status = "[x]" if criterion.is_completed else "[ ]"
                    f.write(f"{i + 1}. {status} {criterion.content}\n")
        except Exception as e:
            print(f"Error saving criteria: {e}")

    def add_criterion(self, criterion: Criterion) -> int:
        """
        Add a criterion and return its index
        If the criterion already exists, return its index
        """
        # Check if criterion already exists
        for i, existing_criterion in enumerate(self.criteria):
            if existing_criterion.content == criterion.content:
                return i

        # Add new criterion
        self.criteria.append(criterion)
        self.save()
        return len(self.criteria) - 1

    def mark_criterion_as_done(self, index: int) -> bool:
        """
        Mark criterion as done and return success

        Args:
            index: Index of the criterion to mark as done

        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.criteria):
            self.criteria[index].is_completed = True
            self.save()
            return True
        return False

    def get_criteria_met_count(self) -> int:
        """Get the number of criteria met"""
        count = 0
        for criterion in self.criteria:
            if criterion.is_completed:
                count += 1
        return count

    def get_criteria_total_count(self) -> int:
        """Get the total number of criteria"""
        return len(self.criteria)
