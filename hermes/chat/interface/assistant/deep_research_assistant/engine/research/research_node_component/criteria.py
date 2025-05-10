from dataclasses import dataclass


@dataclass
class Criterion:
    """A criterion for determining if a problem is done"""
    
    content: str
    is_completed: bool = False
