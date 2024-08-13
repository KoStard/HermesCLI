from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PromptFormatter(ABC):
    @abstractmethod
    def format_prompt(self, files: Dict[str, str], prompt: str, special_command: Optional[Dict[str, str]] = None) -> Any:
        pass
    
    @abstractmethod
    def add_content(self, current, content_to_add: str) -> Any:
        pass
