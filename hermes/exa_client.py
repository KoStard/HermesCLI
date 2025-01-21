from exa_py import Exa
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class ExaContentResult:
    url: str
    text: str
    id: str
    title: str
    author: Optional[str]
    published_date: Optional[str]
    image: Optional[str]

class ExaClient:
    def __init__(self, api_key: str):
        self.client = Exa(api_key=api_key)
    
    def get_contents(self, url: str, text: bool = True) -> List[ExaContentResult]:
        """Get contents of a URL with error handling and validation"""
        response = self.client.get_contents([url], text=text)
        return [
            ExaContentResult(
                url=result.url,
                text=result.text,
                id=result.id,
                title=result.title,
                author=result.author,
                published_date=result.published_date,
                image=result.image
            ) for result in response.results
        ]
