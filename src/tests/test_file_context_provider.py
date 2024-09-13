import unittest
from argparse import ArgumentParser
from unittest.mock import MagicMock, patch
from hermes.context_providers.file_context_provider import FileContextProvider
from hermes.prompt_builders.base import PromptBuilder
from hermes.config import HermesConfig

class TestFileContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = FileContextProvider()

    def test_add_argument(self):
        parser = ArgumentParser()
        self.provider.add_argument(parser)
        args = parser.parse_args(['file1.txt', 'file2.txt'])
        self.assertEqual(args.files, ['file1.txt', 'file2.txt'])

    @patch('os.path.exists')
    def test_load_context_from_cli(self, mock_exists):
        mock_exists.return_value = True
        config = MagicMock(spec=HermesConfig)
        config.get.return_value = ['file1.txt', 'file2.txt']
        self.provider.load_context_from_cli(config)
        self.assertEqual(self.provider.file_paths, ['file1.txt', 'file2.txt'])

    @patch('os.path.exists')
    def test_load_context_interactive(self, mock_exists):
        mock_exists.return_value = True
        self.provider.load_context_interactive('file3.txt')
        self.assertEqual(self.provider.file_paths, ['file3.txt'])

    @patch('hermes.utils.file_utils.process_file_name')
    def test_add_to_prompt(self, mock_process_file_name):
        self.provider.file_paths = ['file1.txt', 'file2.txt']
        mock_process_file_name.side_effect = lambda x: x.split('.')[0]
        prompt_builder = MagicMock(spec=PromptBuilder)
        self.provider.add_to_prompt(prompt_builder)
        prompt_builder.add_file.assert_any_call('file1.txt', 'file1')
        prompt_builder.add_file.assert_any_call('file2.txt', 'file2')
        self.assertEqual(prompt_builder.add_file.call_count, 2)

if __name__ == '__main__':
    unittest.main()
