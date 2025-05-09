from . import ResearchNode


class ResearchNodeImpl(ResearchNode):
    children: list[ResearchNode]

    def __init__(self) -> None:
        self.children = []
