import unittest
from unittest.mock import Mock, patch
import argparse
from hermes.meta_context_providers.help_context_provider import HelpContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestHelpContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = HelpContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        with self.assertRaises(NotImplementedError):
            HelpContextProvider.add_argument(Mock(spec=argparse.ArgumentParser))

    def test_load_context_from_cli(self):
        with self.assertRaises(NotImplementedError):
            self.provider.load_context_from_cli(Mock(spec=argparse.Namespace))

    @patch('builtins.print')
    def test_load_context_from_string_simple_mode(self, mock_print):
        self.provider.load_context_from_string([])
        self.assertTrue(self.provider.loaded)
        self.assertIsNone(self.provider.help_request)
        mock_print.assert_called_once()

    def test_load_context_from_string_with_args(self):
        self.provider.load_context_from_string(['command1', 'command2'])
        self.assertTrue(self.provider.loaded)
        self.assertEqual(self.provider.help_request, 'command1 command2')

    def test_add_to_prompt_simple_mode(self):
        self.provider.load_context_from_string([])
        self.provider.add_to_prompt(self.mock_prompt_builder)
        self.mock_prompt_builder.add_text.assert_called_once()

    def test_add_to_prompt_with_help_request(self):
        self.provider.load_context_from_string(['command1'])
        self.provider.add_to_prompt(self.mock_prompt_builder)
        self.assertEqual(self.mock_prompt_builder.add_text.call_count, 2)

    def test_get_command_key(self):
        self.assertEqual(HelpContextProvider.get_command_key(), "help")

    def test_get_required_providers_simple_mode(self):
        self.provider.load_context_from_string([])
        self.assertEqual(self.provider.get_required_providers(), {})

    def test_get_required_providers_with_help_request(self):
        self.provider.load_context_from_string(['command1'])
        self.assertEqual(self.provider.get_required_providers(), {'prefill': ['hermes_assistant']})

    def test_counts_as_input(self):
        self.provider.load_context_from_string([])
        self.assertFalse(self.provider.counts_as_input())
        
        self.provider.load_context_from_string(['command1'])
        self.assertTrue(self.provider.counts_as_input())

    def test_get_help(self):
        self.assertEqual(HelpContextProvider.get_help(), "Show help from chat")

if __name__ == '__main__':
    unittest.main()