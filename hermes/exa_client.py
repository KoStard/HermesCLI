from dataclasses import dataclass


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
    def __init__(self, api_key: str):
        from exa_py import Exa

        self.client = Exa(api_key=api_key)

    def get_contents(self, url: str, text: bool = True) -> list[ExaContentResult]:
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
                image=result.image,
            )
            for result in response.results
        ]

    def search(self, query: str, num_results: int = 10) -> list[ExaContentResult]:
        """Search for a query and return the results"""
        response = self.client.search(query, num_results=num_results)
        return [
            ExaSearchResult(
                url=result.url,
                title=result.title,
                author=result.author,
                published_date=result.published_date,
            )
            for result in response.results
        ]
