import pytest
from unittest.mock import Mock, patch
from argparse import ArgumentParser
from requests.exceptions import RequestException

from hermes.context_providers.url_context_provider import URLContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestURLContextProvider:
    @pytest.fixture
    def url_provider(self):
        return URLContextProvider()

    def test_add_argument(self, url_provider):
        parser = ArgumentParser()
        url_provider.add_argument(parser)
        args = parser.parse_args(['--url', 'http://example.com'])
        assert args.url == ['http://example.com']

    @patch('requests.get')
    def test_fetch_url_content_success(self, mock_get, url_provider):
        mock_response = Mock()
        mock_response.text = '<html><body><h1>Test</h1></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        content = url_provider.fetch_url_content('http://example.com')
        assert 'Test' in content
        mock_get.assert_called_once_with('http://example.com')

    @patch('requests.get')
    def test_fetch_url_content_retry(self, mock_get, url_provider):
        mock_response = Mock()
        mock_response.text = '<html><body><h1>Test</h1></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.side_effect = [RequestException, RequestException, mock_response]

        content = url_provider.fetch_url_content('http://example.com')
        assert 'Test' in content
        assert mock_get.call_count == 3

    @patch('requests.get')
    def test_fetch_url_content_failure(self, mock_get, url_provider):
        mock_get.side_effect = RequestException

        with pytest.raises(RequestException):
            url_provider.fetch_url_content('http://example.com')

    def test_load_context(self, url_provider):
        args = Mock()
        args.url = ['http://example.com', 'http://test.com']
        
        with patch.object(url_provider, 'fetch_url_content') as mock_fetch:
            mock_fetch.side_effect = ['Content 1', 'Content 2']
            url_provider.load_context(args)

        assert url_provider.urls == ['http://example.com', 'http://test.com']
        assert url_provider.contents == ['Content 1', 'Content 2']

    def test_add_to_prompt(self, url_provider):
        url_provider.urls = ['http://example.com', 'http://test.com']
        url_provider.contents = ['Content 1', 'Content 2']
        
        mock_prompt_builder = Mock(spec=PromptBuilder)
        url_provider.add_to_prompt(mock_prompt_builder)

        mock_prompt_builder.add_text.assert_any_call('Content 1', name='URL: http://example.com')
        mock_prompt_builder.add_text.assert_any_call('Content 2', name='URL: http://test.com')

    def test_html_to_markdown(self, url_provider):
        html = '<html><body><h1>Test</h1><p>This is a test.</p></body></html>'
        markdown = url_provider.html_to_markdown(html)
        assert '# Test' in markdown
        assert 'This is a test.' in markdown
