import unittest
from unittest.mock import MagicMock, Mock, patch
import argparse
from hermes.context_providers.eml_context_provider import EMLContextProvider
from hermes.prompt_builders.base import PromptBuilder

class TestEMLContextProvider(unittest.TestCase):
    def setUp(self):
        self.provider = EMLContextProvider()
        self.mock_prompt_builder = Mock(spec=PromptBuilder)

    def test_add_argument(self):
        mock_parser = Mock(spec=argparse.ArgumentParser)
        EMLContextProvider.add_argument(mock_parser)
        mock_parser.add_argument.assert_called_once_with('--eml', nargs='*', help=EMLContextProvider.get_help())

    def test_get_help(self):
        self.assertEqual(EMLContextProvider.get_help(), 'EML (email) files to be included in the context')

    @patch('glob.glob')
    @patch('os.path.exists')
    def test_load_context_from_cli(self, mock_exists, mock_glob):
        mock_glob.return_value = ['email1.eml', 'email2.eml']
        mock_exists.return_value = True

        args = Mock(spec=argparse.Namespace)
        args.eml = ['*.eml']
        
        self.provider.load_context_from_cli(args)
        
        self.assertEqual(self.provider.eml_paths, ['email1.eml', 'email2.eml'])

    @patch('glob.glob')
    @patch('os.path.exists')
    def test_load_context_from_string(self, mock_exists, mock_glob):
        mock_glob.return_value = ['email1.eml', 'email2.eml']
        mock_exists.return_value = True

        self.provider.load_context_from_string(['*.eml'])
        
        self.assertEqual(self.provider.eml_paths, ['email1.eml', 'email2.eml'])

    @patch('hermes.context_providers.eml_context_provider.EMLContextProvider._parse_eml_file')
    def test_add_to_prompt(self, mock_parse_eml):
        mock_parse_eml.return_value = "Parsed EML content"
        self.provider.eml_paths = ['email1.eml']

        self.provider.add_to_prompt(self.mock_prompt_builder)
        
        self.mock_prompt_builder.add_text.assert_called_once_with("Parsed EML content", "email1")

    @patch('email.message_from_binary_file')
    def test_parse_eml_file(self, mock_message_from_binary_file):
        mock_msg = MagicMock()
        mock_msg.__getitem__.side_effect = lambda x: f"Mock {x}"
        mock_msg.is_multipart.return_value = False
        mock_msg.get_payload.return_value = b"Mock body content"
        mock_message_from_binary_file.return_value = mock_msg

        with patch('builtins.open', unittest.mock.mock_open()):
            result = self.provider._parse_eml_file('test.eml')

        expected_result = "\n".join([
            "From: Mock from",
            "To: Mock to",
            "Subject: Mock subject",
            "Date: Mock date",
            "\nBody:",
            "Mock body content"
        ])
        self.assertEqual(result, expected_result)

    def test_get_command_key(self):
        self.assertEqual(EMLContextProvider.get_command_key(), ["eml"])

if __name__ == '__main__':
    unittest.main()
