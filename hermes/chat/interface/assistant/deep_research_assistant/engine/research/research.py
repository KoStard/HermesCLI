from pathlib import Path

from . import Research


class ResearchImpl(Research):
    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory
