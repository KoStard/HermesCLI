import unittest
from unittest.mock import Mock
import argparse
from hermes.context_providers.text_context_provider import TextContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestTextContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = TextContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        TextContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with('--text', type=str, action='append', help=TextContextProvider.get_help())

    def test_get_help(self):
        self.assertEqual(TextContextProvider.get_help(), 'Text to be included in the context (can be used multiple times)')

    def test_load_context_from_cli_single(self):
        args = Mock(spec=argparse.Namespace)
        args.text = "Sample text"
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.texts, ["Sample text"])

    def test_load_context_from_cli_multiple(self):
        args = Mock(spec=argparse.Namespace)
        args.text = ["Text 1", "Text 2"]
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.texts, ["Text 1", "Text 2"])

    def test_load_context_from_string(self):
        self.provider.load_context_from_string(["Text 1", "Text 2"])
        
        self.assertEqual(self.provider.texts, ["Text 1 Text 2"])

    def test_add_to_prompt(self):
        self.provider.texts = ["Text 1", "Text 2"]
        
        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_text.assert_any_call("Text 1", name="CLI Text Input 1")
        self.mock_prompt_builder.add_text.assert_any_call("Text 2", name="CLI Text Input 2")

    def test_get_command_key(self):
        self.assertEqual(TextContextProvider.get_command_key(), "text")

    def test_serialize(self):
        self.provider.texts = ["Text 1", "Text 2"]
        serialized = self.provider.serialize()
        self.assertEqual(serialized, {"texts": ["Text 1", "Text 2"]})

    def test_deserialize(self):
        data = {"texts": ["Text 3", "Text 4"]}
        self.provider.deserialize(data)
        self.assertEqual(self.provider.texts, ["Text 3", "Text 4"])

if __name__ == '__main__':
    unittest.main()
