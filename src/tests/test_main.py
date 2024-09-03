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
from hermes.prompt_formatters.xml import XMLPromptFormatter
from hermes.prompt_formatters.bedrock import BedrockPromptFormatter

class TestCreateModelAndProcessors(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()

    def test_claude_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("claude", self.config)
        self.assertIsInstance(model, ClaudeModel)
        self.assertIsInstance(file_processor, DefaultFileProcessor)
        self.assertIsInstance(prompt_formatter, XMLPromptFormatter)

    def test_bedrock_models(self):
        bedrock_models = ["bedrock-claude", "bedrock-claude-3.5", "bedrock-opus", "bedrock-mistral"]
        for model_name in bedrock_models:
            model, file_processor, prompt_formatter = create_model_and_processors(model_name, self.config)
            self.assertIsInstance(model, BedrockModel)
            self.assertEqual(model.model_tag, model_name.split("-", 1)[1])
            self.assertIsInstance(file_processor, BedrockFileProcessor)
            self.assertIsInstance(prompt_formatter, BedrockPromptFormatter)

    def test_other_models(self):
        model_classes = {
            "gemini": GeminiModel,
            "openai": OpenAIModel,
            "ollama": OllamaModel
        }
        for model_name, model_class in model_classes.items():
            model, file_processor, prompt_formatter = create_model_and_processors(model_name, self.config)
            self.assertIsInstance(model, model_class)
            self.assertIsInstance(file_processor, DefaultFileProcessor)
            self.assertIsInstance(prompt_formatter, XMLPromptFormatter)

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
    def test_run_chat_application_basic(self, mock_get_default_model, mock_create, mock_ChatUI, mock_ChatApplication):
        mock_get_default_model.return_value = "claude"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        run_chat_application(self.args, self.config, special_command_prompts)
        mock_get_default_model.assert_called_once_with(self.config)
        mock_create.assert_called_once_with("claude", self.config)
        mock_ChatApplication.return_value.run.assert_called_once_with(None, None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_files(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.files = ["file1.txt", "file2.txt"]
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        run_chat_application(self.args, self.config, special_command_prompts)
        mock_ChatApplication.return_value.set_files.assert_called_once()

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_prompt(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.prompt = "Test prompt"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        run_chat_application(self.args, self.config, special_command_prompts)
        mock_ChatApplication.return_value.run.assert_called_once_with("Test prompt", None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="File prompt content")
    def test_run_chat_application_with_prompt_file(self, mock_file, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.prompt_file = "prompt.txt"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        run_chat_application(self.args, self.config, special_command_prompts)
        mock_ChatApplication.return_value.run.assert_called_once_with("File prompt content", None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_special_commands(self, mock_create, mock_ChatUI, mock_ChatApplication):
        test_cases = [
            ('append', 'output.txt', {'append': 'output'}),
            ('update', 'update.txt', {'update': 'update'})
        ]
        for attr, value, expected in test_cases:
            setattr(self.args, attr, value)
            mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
            special_command_prompts = {}
            run_chat_application(self.args, self.config, special_command_prompts)
            mock_ChatApplication.return_value.run.assert_called_with(None, expected)
            setattr(self.args, attr, None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_raw_output(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.pretty = False
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        run_chat_application(self.args, self.config, special_command_prompts)
        mock_ChatUI.assert_called_once_with(prints_raw=True)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_text_inputs(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.text = ["Text input 1", "Text input 2"]
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())
        special_command_prompts = {}
        run_chat_application(self.args, self.config, special_command_prompts)
        mock_ChatApplication.assert_called_once_with(mock_create.return_value[0], mock_ChatUI.return_value,
                                                     mock_create.return_value[1], mock_create.return_value[2],
                                                     special_command_prompts, ["Text input 1", "Text input 2"])

if __name__ == '__main__':
    unittest.main()
