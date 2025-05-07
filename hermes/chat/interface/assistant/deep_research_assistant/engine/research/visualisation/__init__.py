from abc import ABC, abstractmethod


class ResearchTreeVisualizer(ABC):
    @abstractmethod
    def visualize_hierarchy(self) -> str:
        pass
