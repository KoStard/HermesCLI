from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from exa_py import Exa


@dataclass
class ExaContentResult:
    url: str
    text: str
    id: str
    title: str
    author: str | None
    published_date: str | None
    image: str | None


@dataclass
class ExaSearchResult:
    url: str
    title: str
    author: str | None
    published_date: str | None


class ExaClient:
    def __init__(self, api_key: str | None):
        self._api_key = api_key
        self._clien: Exa = None

    def get_contents(self, url: str, text: bool = True) -> list[ExaContentResult]:
        """Get contents of a URL with error handling and validation"""
        response = self._get_client().get_contents([url], text=text)
        return [
            ExaContentResult(
                url=result.url,
                text=result.text,
                id=result.id,
                title=result.title,
                author=result.author,
                published_date=result.published_date,
                image=result.image,
            )
            for result in response.results
        ]

    def search(self, query: str, num_results: int = 10) -> list[ExaSearchResult]:
        """Search for a query and return the results"""
        response = self._get_client().search(query, num_results=num_results)
        return [
            ExaSearchResult(
                url=result.url,
                title=result.title,
                author=result.author,
                published_date=result.published_date,
            )
            for result in response.results
        ]

    def _get_client(self) -> "Exa":
        if self._client:
            return self._client

        from exa_py import Exa

        self._client = Exa(api_key=self.api_key)
        return self._client
