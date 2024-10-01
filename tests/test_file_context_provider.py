import unittest
from unittest.mock import Mock, patch
import argparse
import os
from hermes.context_providers.file_context_provider import FileContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestFileContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = FileContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        FileContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with('files', nargs='*', help=FileContextProvider.get_help())

    def test_get_help(self):
        self.assertEqual(FileContextProvider.get_help(), 'Files to be included in the context')

    @patch('glob.glob')
    @patch('os.path.exists')
    def test_load_context_from_cli(self, mock_exists, mock_glob):
        mock_glob.return_value = ['file1.txt', 'file2.txt']
        mock_exists.return_value = True

        args = Mock(spec=argparse.Namespace)
        args.files = ['*.txt']
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.file_paths, ['file1.txt', 'file2.txt'])

    @patch('glob.glob')
    @patch('os.path.exists')
    def test_load_context_from_string(self, mock_exists, mock_glob):
        mock_glob.return_value = ['file1.txt', 'file2.txt']
        mock_exists.return_value = True

        self.provider.load_context_from_string(['*.txt'])
        
        self.assertEqual(self.provider.file_paths, ['file1.txt', 'file2.txt'])

    @patch('os.path.isdir')
    @patch('os.walk')
    def test_add_to_prompt_file(self, mock_walk, mock_isdir):
        mock_isdir.return_value = False
        self.provider.file_paths = ['file1.txt']

        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_file.assert_called_once_with('file1.txt', 'file1')

    @patch('os.path.isdir')
    @patch('os.walk')
    def test_add_to_prompt_directory(self, mock_walk, mock_isdir):
        mock_isdir.return_value = True
        mock_walk.return_value = [
            ('/root', [], ['file1.txt', 'file2.txt']),
        ]
        self.provider.file_paths = ['/root']

        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_file.assert_any_call('/root/file1.txt', 'file1')
        self.mock_prompt_builder.add_file.assert_any_call('/root/file2.txt', 'file2')

    def test_get_command_key(self):
        self.assertEqual(FileContextProvider.get_command_key(), ["file", "files"])

if __name__ == '__main__':
    unittest.main()
