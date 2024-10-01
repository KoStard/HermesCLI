import unittest
from unittest.mock import Mock, patch
import argparse
import os
from hermes.context_providers.prefill_context_provider import PrefillContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestPrefillContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = PrefillContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        PrefillContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with('--prefill', action="append", help=PrefillContextProvider.get_help())

    @patch.object(PrefillContextProvider, '_load_prefill_map')
    def test_get_help(self, mock_load_prefill_map):
        mock_load_prefill_map.return_value = {'prefill1': 'path1', 'prefill2': 'path2'}
        help_text = PrefillContextProvider.get_help()
        self.assertIn('prefill1', help_text)
        self.assertIn('prefill2', help_text)

    @patch.object(PrefillContextProvider, '_load_prefill_map')
    @patch.object(PrefillContextProvider, '_parse_prefill_file')
    def test_load_context_from_cli(self, mock_parse_prefill_file, mock_load_prefill_map):
        mock_load_prefill_map.return_value = {'prefill1': 'path1'}
        self.provider.prefill_map = mock_load_prefill_map.return_value
        args = Mock(spec=argparse.Namespace)
        args.prefill = ['prefill1']
        
        self.provider.load_context_from_cli(args)
        
        mock_parse_prefill_file.assert_called_once_with('path1')

    @patch.object(PrefillContextProvider, '_load_prefill_map')
    @patch.object(PrefillContextProvider, '_parse_prefill_file')
    def test_load_context_from_string(self, mock_parse_prefill_file, mock_load_prefill_map):
        mock_load_prefill_map.return_value = {'prefill1': 'path1'}
        self.provider.prefill_map = mock_load_prefill_map.return_value
        
        self.provider.load_context_from_string(['prefill1'])
        
        mock_parse_prefill_file.assert_called_once_with('path1')

    @patch('builtins.open')
    def test_parse_prefill_file(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = """---
required_context_providers:
  provider1: [arg1, arg2]
---
Prefill content
"""
        self.provider._parse_prefill_file('fake_path')
        
        self.assertEqual(self.provider.prefill_contents, ['Prefill content'])
        self.assertEqual(self.provider.required_providers, {'provider1': ['arg1', 'arg2']})

    def test_add_to_prompt(self):
        self.provider.prefill_contents = ['Content 1', 'Content 2']
        
        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_text.assert_any_call('Content 1')
        self.mock_prompt_builder.add_text.assert_any_call('Content 2')

    def test_get_command_key(self):
        self.assertEqual(PrefillContextProvider.get_command_key(), "prefill")

    def test_get_required_providers(self):
        self.provider.required_providers = {'provider1': ['arg1', 'arg2']}
        self.assertEqual(self.provider.get_required_providers(), {'provider1': ['arg1', 'arg2']})

    @patch('os.path.exists')
    @patch('os.listdir')
    def test_load_prefill_map(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = ['prefill1.md', 'prefill2.md']
        
        prefill_map = PrefillContextProvider._load_prefill_map()
        
        self.assertIn('prefill1', prefill_map)
        self.assertIn('prefill2', prefill_map)

if __name__ == '__main__':
    unittest.main()