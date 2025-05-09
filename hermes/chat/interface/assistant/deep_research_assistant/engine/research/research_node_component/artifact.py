
from dataclasses import dataclass


@dataclass
class Artifact:
    name: str
    content: str
    short_summary: str
    is_external: bool = False
