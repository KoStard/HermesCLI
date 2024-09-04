import unittest
from argparse import ArgumentParser
from unittest.mock import MagicMock
from hermes.context_providers.text_context_provider import TextContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestTextContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = TextContextProvider()

    def test_add_argument(self):
        parser = ArgumentParser()
        self.provider.add_argument(parser)
        args = parser.parse_args(['--text', 'Sample text'])
        self.assertEqual(args.text, 'Sample text')

    def test_load_context(self):
        args = MagicMock()
        args.text = 'Sample text'
        self.provider.load_context(args)
        self.assertEqual(self.provider.text, 'Sample text')

    def test_load_context_empty(self):
        args = MagicMock()
        args.text = None
        self.provider.load_context(args)
        self.assertEqual(self.provider.text, "")

    def test_add_to_prompt(self):
        self.provider.text = 'Sample text'
        prompt_builder = MagicMock(spec=PromptBuilder)
        self.provider.add_to_prompt(prompt_builder)
        prompt_builder.add_text.assert_called_once_with('Sample text', name="CLI Text Input")

    def test_add_to_prompt_empty(self):
        self.provider.text = ''
        prompt_builder = MagicMock(spec=PromptBuilder)
        self.provider.add_to_prompt(prompt_builder)
        prompt_builder.add_text.assert_not_called()

if __name__ == '__main__':
    unittest.main()
