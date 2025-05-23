import configparser
import os
from argparse import Namespace

from hermes.chat.interface.user.control_panel.exa_client import ExaClient


class UtilsCommandExecutor:
    def __init__(self, config: configparser.ConfigParser):
        self.config = config

    def execute(self, cli_args: Namespace, extension_utils_visitors: list):
        if cli_args.utils_command == "extract_pdf_pages":
            self._extract_pdf_pages(cli_args)
        elif cli_args.utils_command == "get_url":
            self._get_url(cli_args)
        elif cli_args.utils_command == "get_url_exa":
            self._get_url_exa(cli_args)
        elif cli_args.utils_command == "exa_search":
            self._exa_search(cli_args)
        else:
            self._execute_extension_utils(cli_args, extension_utils_visitors)

    def _extract_pdf_pages(self, cli_args: Namespace):
        pages = []
        pages_str = cli_args.pages.strip("{}")
        for part in pages_str.split(","):
            if ":" in part:
                start, end = map(int, part.split(":"))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(part))

        from PyPDF2 import PdfReader, PdfWriter

        reader = PdfReader(cli_args.filepath)
        writer = PdfWriter()

        for page_num in pages:
            if 1 <= page_num <= len(reader.pages):
                writer.add_page(reader.pages[page_num - 1])

        output_path = f"{os.path.splitext(cli_args.filepath)[0]}_extracted.pdf"
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        print(f"Extracted pages saved to: {output_path}")

    def _get_url(self, cli_args: Namespace):
        import requests
        from markitdown import MarkItDown

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        response = requests.get(cli_args.url, headers=headers)
        response.raise_for_status()
        markitdown = MarkItDown()
        conversion_result = markitdown.convert(response)
        markdown_content = conversion_result.text_content
        print(f"\n# URL Content: {cli_args.url}\n")
        print(markdown_content)

    def _get_url_exa(self, cli_args: Namespace):
        client = ExaClient(self.config["EXA"]["api_key"])
        result = client.get_contents(cli_args.url)

        if not result:
            raise ValueError(f"No content found for URL: {cli_args.url}")

        print(f"\n# Exa AI Summary: {cli_args.url}\n")
        print(result[0].title)
        print(result[0].text)
        print("Last updated:", result[0].published_date)

    def _exa_search(self, cli_args: Namespace):
        client = ExaClient(self.config["EXA"]["api_key"])
        results = client.search(cli_args.query, cli_args.num_results)

        if not results:
            print("No results found")
            return

        print(f"\n# Exa Search Results for: {cli_args.query}\n")
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  Title: {result.title}")
            print(f"  URL: {result.url}")
            if result.author:
                print(f"  Author: {result.author}")
            if result.published_date:
                print(f"  Published: {result.published_date}")
            print()

    def _execute_extension_utils(self, cli_args: Namespace, extension_utils_visitors: list):
        for extension_util_visitor in extension_utils_visitors:
            extension_util_visitor(cli_args, self.config)
