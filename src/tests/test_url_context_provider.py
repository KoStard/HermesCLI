import unittest
from unittest.mock import Mock, patch
from argparse import ArgumentParser
from requests.exceptions import RequestException
from tenacity import RetryError

from hermes.config import HermesConfig
from hermes.context_providers.url_context_provider import URLContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestURLContextProvider(unittest.TestCase):
    def setUp(self):
        self.url_provider = URLContextProvider()

    def test_add_argument(self):
        parser = ArgumentParser()
        self.url_provider.add_argument(parser)
        args = parser.parse_args(['--url', 'http://example.com'])
        self.assertEqual(args.url, ['http://example.com'])

    @patch('requests.get')
    def test_fetch_url_content_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = '<html><body><h1>Test</h1></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        content = self.url_provider.fetch_url_content('http://example.com')
        self.assertIn('Test', content)
        mock_get.assert_called_once_with('http://example.com')

    def test_load_context(self):
        args = HermesConfig({
            'url': ['http://example.com', 'http://test.com']
        })
        
        with patch.object(self.url_provider, 'fetch_url_content') as mock_fetch:
            mock_fetch.side_effect = ['Content 1', 'Content 2']
            self.url_provider.load_context(args)

        self.assertEqual(self.url_provider.urls, ['http://example.com', 'http://test.com'])
        self.assertEqual(self.url_provider.contents, ['Content 1', 'Content 2'])

    def test_add_to_prompt(self):
        self.url_provider.urls = ['http://example.com', 'http://test.com']
        self.url_provider.contents = ['Content 1', 'Content 2']
        
        mock_prompt_builder = Mock(spec=PromptBuilder)
        self.url_provider.add_to_prompt(mock_prompt_builder)

        mock_prompt_builder.add_text.assert_any_call('Content 1', name='URL: http://example.com')
        mock_prompt_builder.add_text.assert_any_call('Content 2', name='URL: http://test.com')

    def test_html_to_markdown(self):
        html = '<html><body><h1>Test</h1><p>This is a test.</p></body></html>'
        markdown = self.url_provider.html_to_markdown(html)
        self.assertIn('# Test', markdown)
        self.assertIn('This is a test.', markdown)

if __name__ == '__main__':
    unittest.main()
