from abc import ABC, abstractmethod


class ResearchNode(ABC):
    pass


class Research(ABC):
    @abstractmethod
    def research_already_exists(self):
        pass

    @abstractmethod
    def create_research(self) -> ResearchNode:
        pass

    @abstractmethod
    def load_existing_research(self) -> ResearchNode:
        pass
