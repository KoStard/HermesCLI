import requests
from argparse import ArgumentParser
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import html2text

from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class URLContextProvider(ContextProvider):
    def __init__(self):
        self.urls: List[str] = []
        self.contents: List[str] = []
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_tables = False

    def add_argument(self, parser: ArgumentParser):
        parser.add_argument("--url", action="append", help="URL to fetch content from")

    def load_context(self, args):
        if args.url:
            self.urls = args.url
            for url in self.urls:
                content = self.fetch_url_content(url)
                self.contents.append(content)

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for url, content in zip(self.urls, self.contents):
            prompt_builder.add_text(content, name=f"URL: {url}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_url_content(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return self.html_to_markdown(response.text)

    def html_to_markdown(self, html: str) -> str:
        return self.html_converter.handle(html)
