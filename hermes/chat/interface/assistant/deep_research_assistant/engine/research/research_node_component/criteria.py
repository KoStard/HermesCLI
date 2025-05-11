from dataclasses import dataclass


@dataclass
class Criterion:
    """A criterion for determining if a problem is done"""
    
    content: str
    is_completed: bool = False
    
    def complete(self) -> None:
        """Mark this criterion as completed"""
        self.is_completed = True
        
    def uncomplete(self) -> None:
        """Mark this criterion as not completed"""
        self.is_completed = False
        
    @staticmethod
    def from_string(content: str, is_completed: bool = False) -> "Criterion":
        """Create a criterion from a string and completion status"""
        return Criterion(content=content, is_completed=is_completed)
