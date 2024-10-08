import argparse
import requests
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from markdownify import markdownify as md
import logging

from hermes.context_providers.base import ContextProvider
from hermes.prompt_builders.base import PromptBuilder

class URLContextProvider(ContextProvider):
    def __init__(self):
        self.urls: List[str] = []
        self.contents: List[str] = []
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def add_argument(parser: ArgumentParser):
        parser.add_argument("--url", action="append", help=URLContextProvider.get_help())

    @staticmethod
    def get_help() -> str:
        return "URL to fetch content from"

    def load_context_from_cli(self, args: argparse.Namespace):
        if args.url:
            self.urls = args.url if isinstance(args.url, list) else [args.url]
            for url in self.urls:
                content = self.fetch_url_content(url)
                self.contents.append(content)
        self.logger.debug(f"Loaded and fetched content for {len(self.urls)} URLs from CLI arguments")

    def load_context_from_string(self, urls: List[str]):
        for url in urls:
            content = self.fetch_url_content(url)
            self.urls.append(url)
            self.contents.append(content)
        self.logger.debug(f"Added and fetched content for {len(urls)} URLs interactively")

    def add_to_prompt(self, prompt_builder: PromptBuilder):
        for url, content in zip(self.urls, self.contents):
            prompt_builder.add_text(content, name=f"URL: {url}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_url_content(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return self.html_to_markdown(response.text)

    def html_to_markdown(self, html: str) -> str:
        return md(html, heading_style='atx')

    @staticmethod
    def get_command_key() -> str:
        return "url"

    def serialize(self) -> Dict[str, Any]:
        return {
            "urls": self.urls,
            "contents": self.contents
        }

    def deserialize(self, data: Dict[str, Any]):
        self.urls = data.get("urls", [])
        self.contents = data.get("contents", [])
