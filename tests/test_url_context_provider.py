import unittest
from unittest.mock import Mock, patch
import argparse
from hermes.context_providers.url_context_provider import URLContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestURLContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = URLContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        URLContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with("--url", action="append", help=URLContextProvider.get_help())

    def test_get_help(self):
        self.assertEqual(URLContextProvider.get_help(), "URL to fetch content from")

    @patch('requests.get')
    def test_load_context_from_cli(self, mock_get):
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response

        args = Mock(spec=argparse.Namespace)
        args.url = ["http://example.com"]
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.urls, ["http://example.com"])
        self.assertEqual(len(self.provider.contents), 1)
        self.assertIn("Test content", self.provider.contents[0])

    @patch('requests.get')
    def test_load_context_from_string(self, mock_get):
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response

        self.provider.load_context_from_string(["http://example.com"])
        
        self.assertEqual(self.provider.urls, ["http://example.com"])
        self.assertEqual(len(self.provider.contents), 1)
        self.assertIn("Test content", self.provider.contents[0])

    def test_add_to_prompt(self):
        self.provider.urls = ["http://example.com"]
        self.provider.contents = ["Test content"]
        
        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_text.assert_called_once_with("Test content", name="URL: http://example.com")

    @patch('requests.get')
    def test_fetch_url_content(self, mock_get):
        mock_response = Mock()
        mock_response.text = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        mock_get.return_value = mock_response

        content = self.provider.fetch_url_content("http://example.com")
        
        self.assertEqual(content, "# Test\n\nContent\n\n")

    def test_html_to_markdown(self):
        html = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        markdown = self.provider.html_to_markdown(html)
        self.assertEqual(markdown, "# Test\n\nContent\n\n")

    def test_get_command_key(self):
        self.assertEqual(URLContextProvider.get_command_key(), "url")

    def test_serialize(self):
        self.provider.urls = ["http://example.com", "http://test.com"]
        self.provider.contents = ["Example content", "Test content"]
        serialized = self.provider.serialize()
        self.assertEqual(serialized, {
            "urls": ["http://example.com", "http://test.com"],
            "contents": ["Example content", "Test content"]
        })

    def test_deserialize(self):
        data = {
            "urls": ["http://new.com", "http://sample.com"],
            "contents": ["New content", "Sample content"]
        }
        self.provider.deserialize(data)
        self.assertEqual(self.provider.urls, ["http://new.com", "http://sample.com"])
        self.assertEqual(self.provider.contents, ["New content", "Sample content"])

if __name__ == '__main__':
    unittest.main()
