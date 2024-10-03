import unittest
from unittest.mock import Mock, patch
import argparse
from hermes.context_providers.clipboard_context_provider import ClipboardContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestClipboardContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = ClipboardContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        ClipboardContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with('--clipboard', action='store_true', help='Include clipboard content in the context')

    def test_get_help(self):
        self.assertEqual(ClipboardContextProvider.get_help(), 'Include clipboard content in the context')

    @patch('pyperclip.paste')
    def test_load_context_from_cli(self, mock_paste):
        mock_paste.return_value = "Clipboard content"
        args = Mock(clipboard=True)
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.clipboard_content, "Clipboard content")

    @patch('pyperclip.paste')
    def test_load_context_from_string(self, mock_paste):
        mock_paste.return_value = "Clipboard content"

        self.provider.load_context_from_string([])
        
        self.assertEqual(self.provider.clipboard_content, "Clipboard content")

    def test_add_to_prompt(self):
        self.provider.clipboard_content = "Clipboard content"

        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_text.assert_called_once_with("Clipboard Content", "Clipboard content")

    def test_get_command_key(self):
        self.assertEqual(ClipboardContextProvider.get_command_key(), ["clipboard"])

if __name__ == '__main__':
    unittest.main()