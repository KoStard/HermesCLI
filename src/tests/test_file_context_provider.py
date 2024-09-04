import unittest
from argparse import ArgumentParser
from unittest.mock import MagicMock
from hermes.context_providers.file_context_provider import FileContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestFileContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = FileContextProvider()

    def test_add_argument(self):
        parser = ArgumentParser()
        self.provider.add_argument(parser)
        args = parser.parse_args(['file1.txt', 'file2.txt'])
        self.assertEqual(args.files, ['file1.txt', 'file2.txt'])

    def test_load_context(self):
        args = MagicMock()
        args.files = ['file1.txt', 'file2.txt']
        self.provider.load_context(args)
        self.assertEqual(self.provider.files, ['file1.txt', 'file2.txt'])

    def test_add_to_prompt(self):
        self.provider.files = ['file1.txt', 'file2.txt']
        prompt_builder = MagicMock(spec=PromptBuilder)
        self.provider.add_to_prompt(prompt_builder)
        prompt_builder.add_file.assert_any_call('file1.txt')
        prompt_builder.add_file.assert_any_call('file2.txt')
        self.assertEqual(prompt_builder.add_file.call_count, 2)

if __name__ == '__main__':
    unittest.main()
