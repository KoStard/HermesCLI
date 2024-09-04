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
        args = parser.parse_args(['--text', 'Sample text 1', '--text', 'Sample text 2'])
        self.assertEqual(args.text, ['Sample text 1', 'Sample text 2'])

    def test_load_context(self):
        args = MagicMock()
        args.text = ['Sample text 1', 'Sample text 2']
        self.provider.load_context(args)
        self.assertEqual(self.provider.texts, ['Sample text 1', 'Sample text 2'])

    def test_load_context_empty(self):
        args = MagicMock()
        args.text = None
        self.provider.load_context(args)
        self.assertEqual(self.provider.texts, [])

    def test_add_to_prompt(self):
        self.provider.texts = ['Sample text 1', 'Sample text 2']
        prompt_builder = MagicMock(spec=PromptBuilder)
        self.provider.add_to_prompt(prompt_builder)
        prompt_builder.add_text.assert_any_call('Sample text 1', name="CLI Text Input 1")
        prompt_builder.add_text.assert_any_call('Sample text 2', name="CLI Text Input 2")
        self.assertEqual(prompt_builder.add_text.call_count, 2)

    def test_add_to_prompt_empty(self):
        self.provider.texts = []
        prompt_builder = MagicMock(spec=PromptBuilder)
        self.provider.add_to_prompt(prompt_builder)
        prompt_builder.add_text.assert_not_called()

if __name__ == '__main__':
    unittest.main()
