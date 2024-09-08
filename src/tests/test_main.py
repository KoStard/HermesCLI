import unittest
import configparser
from unittest.mock import patch, MagicMock
from hermes.config import HermesConfig
from hermes.main import run_chat_application


class TestRunChatApplication(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.args = HermesConfig({
            'pretty': True,
            'raw': False,
        })

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.get_default_model')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_basic(self, mock_ContextOrchestrator, mock_get_default_model, mock_create, mock_ChatUI, mock_ChatApplication):
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, special_command_prompts, mock_context_orchestrator)
        mock_create.assert_called_once_with(None)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_ChatApplication.return_value.run.assert_called_once_with(None, {})

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_with_prompt(self, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.set('prompt', "Test prompt")
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, special_command_prompts, mock_context_orchestrator)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_ChatApplication.return_value.run.assert_called_once_with("Test prompt", {})

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="File prompt content")
    def test_run_chat_application_with_prompt_file(self, mock_file, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.set('prompt_file', "prompt.txt")
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, special_command_prompts, mock_context_orchestrator)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_ChatApplication.return_value.run.assert_called_once_with("File prompt content", {})

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_with_special_commands(self, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        test_cases = [
            ('append', 'output.txt', {'append': 'output.txt'}),
            ('update', 'update.txt', {'update': 'update.txt'})
        ]
        for attr, value, expected in test_cases:
            self.args.set(attr, value)
            mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
            special_command_prompts = {}
            mock_context_orchestrator = MagicMock()
            mock_ContextOrchestrator.return_value = mock_context_orchestrator
            run_chat_application(self.args, special_command_prompts, mock_context_orchestrator)
            mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
            mock_ChatApplication.return_value.run.assert_called_with(None, expected)
            self.args.set(attr, None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_with_raw_output(self, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.set('pretty', False)
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, special_command_prompts, mock_context_orchestrator)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_ChatUI.assert_called_once_with(prints_raw=True)

if __name__ == '__main__':
    unittest.main()
