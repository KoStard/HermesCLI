from . import Research, ResearchNode


class ResearchImpl(Research):
    def __init__(self, root_node: ResearchNode) -> None:
        self.root_node = root_node
