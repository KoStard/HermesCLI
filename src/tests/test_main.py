import unittest
from unittest.mock import patch, MagicMock
import configparser
from hermes.main import create_model_and_processors, run_chat_application
from hermes.chat_models.claude import ClaudeModel
from hermes.chat_models.bedrock import BedrockModel
from hermes.chat_models.gemini import GeminiModel
from hermes.chat_models.openai import OpenAIModel
from hermes.chat_models.ollama import OllamaModel
from hermes.file_processors.default import DefaultFileProcessor
from hermes.file_processors.bedrock import BedrockFileProcessor
from hermes.prompt_builders.xml_prompt_builder import XMLPromptBuilder
from hermes.prompt_builders.bedrock_prompt_builder import BedrockPromptBuilder

class TestCreateModelAndProcessors(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()

    def test_claude_model(self):
        model, file_processor, prompt_builder = create_model_and_processors("claude", self.config)
        self.assertIsInstance(model, ClaudeModel)
        self.assertIsInstance(file_processor, DefaultFileProcessor)
        self.assertIsInstance(prompt_builder, XMLPromptBuilder)

    def test_bedrock_models(self):
        bedrock_models = ["bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral"]
        for model_name in bedrock_models:
            model, file_processor, prompt_builder = create_model_and_processors(model_name, self.config)
            self.assertIsInstance(model, BedrockModel)
            self.assertEqual(model.model_tag, model_name.split("-", 1)[1])
            self.assertIsInstance(file_processor, BedrockFileProcessor)
            self.assertIsInstance(prompt_builder, BedrockPromptBuilder)

    def test_other_models(self):
        model_classes = {
            "gemini": GeminiModel,
            "openai": OpenAIModel,
            "ollama": OllamaModel
        }
        for model_name, model_class in model_classes.items():
            model, file_processor, prompt_builder = create_model_and_processors(model_name, self.config)
            self.assertIsInstance(model, model_class)
            self.assertIsInstance(file_processor, DefaultFileProcessor)
            self.assertIsInstance(prompt_builder, XMLPromptBuilder)

    def test_unsupported_model(self):
        with self.assertRaises(ValueError):
            create_model_and_processors("unsupported-model", self.config)

class TestRunChatApplication(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.args = MagicMock()
        self.args.model = None
        self.args.files = []
        self.args.prompt = None
        self.args.prompt_file = None
        self.args.append = None
        self.args.update = None
        self.args.raw = False
        self.args.pretty = True
        self.args.text = []

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.get_default_model')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_basic(self, mock_ContextOrchestrator, mock_get_default_model, mock_create, mock_ChatUI, mock_ChatApplication):
        mock_get_default_model.return_value = "claude"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, self.config, special_command_prompts, mock_context_orchestrator)
        mock_get_default_model.assert_called_once_with(self.config)
        mock_create.assert_called_once_with("claude", self.config)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_context_orchestrator.build_prompt.assert_called_once()
        mock_ChatApplication.return_value.run.assert_called_once_with(None, None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_with_prompt(self, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.prompt = "Test prompt"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, self.config, special_command_prompts, mock_context_orchestrator)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_context_orchestrator.build_prompt.assert_called_once()
        mock_ChatApplication.return_value.run.assert_called_once_with("Test prompt", None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="File prompt content")
    def test_run_chat_application_with_prompt_file(self, mock_file, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.prompt_file = "prompt.txt"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, self.config, special_command_prompts, mock_context_orchestrator)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_context_orchestrator.build_prompt.assert_called_once()
        mock_ChatApplication.return_value.run.assert_called_once_with("File prompt content", None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_with_special_commands(self, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        test_cases = [
            ('append', 'output.txt', {'append': 'output'}),
            ('update', 'update.txt', {'update': 'update'})
        ]
        for attr, value, expected in test_cases:
            setattr(self.args, attr, value)
            mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
            special_command_prompts = {}
            mock_context_orchestrator = MagicMock()
            mock_ContextOrchestrator.return_value = mock_context_orchestrator
            run_chat_application(self.args, self.config, special_command_prompts, mock_context_orchestrator)
            mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
            mock_context_orchestrator.build_prompt.assert_called_once()
            mock_ChatApplication.return_value.run.assert_called_with(None, expected)
            setattr(self.args, attr, None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('hermes.main.ContextOrchestrator')
    def test_run_chat_application_with_raw_output(self, mock_ContextOrchestrator, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.pretty = False
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        mock_context_orchestrator = MagicMock()
        mock_ContextOrchestrator.return_value = mock_context_orchestrator
        run_chat_application(self.args, self.config, special_command_prompts, mock_context_orchestrator)
        mock_context_orchestrator.load_contexts.assert_called_once_with(self.args)
        mock_context_orchestrator.build_prompt.assert_called_once()
        mock_ChatUI.assert_called_once_with(prints_raw=True)

if __name__ == '__main__':
    unittest.main()
