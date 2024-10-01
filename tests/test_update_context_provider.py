import unittest
from unittest.mock import Mock, patch
import argparse
import os
from hermes.context_providers.update_context_provider import UpdateContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestUpdateContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = UpdateContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        UpdateContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with("--update", "--create", "--write", "-u", "-c", "-w", help=UpdateContextProvider.get_help(), dest="update")

    def test_get_help(self):
        self.assertEqual(UpdateContextProvider.get_help(), "Update or create the specified file")

    @patch('os.path.dirname')
    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_context_from_cli(self, mock_yaml, mock_open, mock_dirname):
        mock_dirname.return_value = '/fake/path'
        mock_yaml.return_value = {'update': '{file_name}'}
        
        args = Mock(spec=argparse.Namespace)
        args.update = "test.txt"
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.file_path, "test.txt")
        self.assertEqual(self.provider.special_command_prompt, "test")

    @patch('os.path.dirname')
    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_context_from_string(self, mock_yaml, mock_open, mock_dirname):
        mock_dirname.return_value = '/fake/path'
        mock_yaml.return_value = {'update': '{file_name}'}
        
        self.provider.load_context_from_string(["test.txt"])
        
        self.assertEqual(self.provider.file_path, "test.txt")
        self.assertEqual(self.provider.special_command_prompt, "test")

    def test_add_to_prompt(self):
        self.provider.file_path = "test.txt"
        self.provider.special_command_prompt = "Update test.txt"
        
        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_text.assert_called_once_with("Update test.txt", "update_command")
        self.mock_prompt_builder.add_file.assert_called_once_with("test.txt", "test.txt")

    def test_get_command_key(self):
        self.assertEqual(UpdateContextProvider.get_command_key(), ["update", "create"])

    def test_counts_as_input(self):
        self.assertTrue(self.provider.counts_as_input())

    def test_is_action(self):
        self.assertTrue(self.provider.is_action())

    @patch('hermes.utils.file_utils.write_file')
    def test_perform_action(self, mock_write_file):
        self.provider.file_path = "test.txt"
        result = self.provider.perform_action("New content")
        
        mock_write_file.assert_called_once_with("test.txt", "New content", mode="w")
        self.assertEqual(result, "File test.txt updated")

if __name__ == '__main__':
    unittest.main()