import unittest
from unittest.mock import patch, MagicMock, mock_open
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

    def test_bedrock_claude_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("bedrock-claude", self.config)
        self.assertIsInstance(model, BedrockModel)
        self.assertEqual(model.model_tag, "claude")
        self.assertIsInstance(file_processor, BedrockFileProcessor)
        self.assertIsInstance(prompt_formatter, BedrockPromptFormatter)

    def test_bedrock_claude_3_5_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("bedrock-claude-3.5", self.config)
        self.assertIsInstance(model, BedrockModel)
        self.assertEqual(model.model_tag, "claude-3.5")
        self.assertIsInstance(file_processor, BedrockFileProcessor)
        self.assertIsInstance(prompt_formatter, BedrockPromptFormatter)

    def test_bedrock_opus_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("bedrock-opus", self.config)
        self.assertIsInstance(model, BedrockModel)
        self.assertEqual(model.model_tag, "opus")
        self.assertIsInstance(file_processor, BedrockFileProcessor)
        self.assertIsInstance(prompt_formatter, BedrockPromptFormatter)

    def test_bedrock_mistral_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("bedrock-mistral", self.config)
        self.assertIsInstance(model, BedrockModel)
        self.assertEqual(model.model_tag, "mistral")
        self.assertIsInstance(file_processor, BedrockFileProcessor)
        self.assertIsInstance(prompt_formatter, BedrockPromptFormatter)

    def test_gemini_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("gemini", self.config)
        self.assertIsInstance(model, GeminiModel)
        self.assertIsInstance(file_processor, DefaultFileProcessor)
        self.assertIsInstance(prompt_formatter, XMLPromptFormatter)

    def test_openai_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("openai", self.config)
        self.assertIsInstance(model, OpenAIModel)
        self.assertIsInstance(file_processor, DefaultFileProcessor)
        self.assertIsInstance(prompt_formatter, XMLPromptFormatter)

    def test_ollama_model(self):
        model, file_processor, prompt_formatter = create_model_and_processors("ollama", self.config)
        self.assertIsInstance(model, OllamaModel)
        self.assertIsInstance(file_processor, DefaultFileProcessor)
        self.assertIsInstance(prompt_formatter, XMLPromptFormatter)

    def test_unsupported_model(self):
        with self.assertRaises(ValueError):
            create_model_and_processors("unsupported-model", self.config)

class TestRunChatApplication(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.args = MagicMock()
        self.args.model = "claude"
        self.args.files = []
        self.args.prompt = None
        self.args.prompt_file = None
        self.args.append = None
        self.args.update = None
        self.args.raw = False
        self.args.confirm_before_starting = False

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_basic(self, mock_create, mock_ChatUI, mock_ChatApplication):
        mock_model = MagicMock()
        mock_file_processor = MagicMock()
        mock_prompt_formatter = MagicMock()
        mock_create.return_value = (mock_model, mock_file_processor, mock_prompt_formatter)

        run_chat_application(self.args, self.config)

        mock_create.assert_called_once_with("claude", self.config)
        mock_ChatUI.assert_called_once_with(prints_raw=False)
        mock_ChatApplication.assert_called_once()
        mock_ChatApplication.return_value.run.assert_called_once_with(None, None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_files(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.files = ["file1.txt", "file2.txt"]
        mock_prompt_formatter = MagicMock()
        mock_create.return_value = (MagicMock(), MagicMock(), mock_prompt_formatter)

        run_chat_application(self.args, self.config)

        mock_prompt_formatter.format_prompt.assert_called_once_with(
            {'file1.txt': 'file1.txt', 'file2.txt': 'file2.txt'},
            None,
            None
        )

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_prompt(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.prompt = "Test prompt"
        mock_prompt_formatter = MagicMock()
        mock_create.return_value = (MagicMock(), MagicMock(), mock_prompt_formatter)

        run_chat_application(self.args, self.config)

        mock_prompt_formatter.format_prompt.assert_called_once_with({}, "Test prompt", None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_prompt_file(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.prompt_file = "prompt.txt"
        mock_prompt_formatter = MagicMock()
        mock_create.return_value = (MagicMock(), MagicMock(), mock_prompt_formatter)

        with patch("builtins.open", mock_open(read_data="File prompt content")) as mock_file:
            run_chat_application(self.args, self.config)

        mock_file.assert_called_once_with("prompt.txt", "r")
        mock_prompt_formatter.format_prompt.assert_called_once_with({}, "File prompt content", None)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_append(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.append = "output.txt"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())

        run_chat_application(self.args, self.config)

        mock_ChatApplication.return_value.run.assert_called_once_with(None, {'append': 'output.txt'})

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_update(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.update = "update.txt"
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())

        run_chat_application(self.args, self.config)

        mock_ChatApplication.return_value.run.assert_called_once_with(None, {'update': 'update.txt'})

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    def test_run_chat_application_with_raw_output(self, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.raw = True
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())

        run_chat_application(self.args, self.config)

        mock_ChatUI.assert_called_once_with(prints_raw=True)

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('builtins.input', return_value='y')
    def test_run_chat_application_with_confirmation(self, mock_input, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.confirm_before_starting = True
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())

        run_chat_application(self.args, self.config)

        mock_input.assert_called_once_with("Are you sure you want to continue? (y/n) ")
        mock_ChatApplication.return_value.run.assert_called_once()

    @patch('hermes.main.ChatApplication')
    @patch('hermes.main.ChatUI')
    @patch('hermes.main.create_model_and_processors')
    @patch('builtins.input', return_value='n')
    def test_run_chat_application_with_confirmation_denied(self, mock_input, mock_create, mock_ChatUI, mock_ChatApplication):
        self.args.confirm_before_starting = True
        mock_create.return_value = (MagicMock(), MagicMock(), MagicMock())

        run_chat_application(self.args, self.config)

        mock_input.assert_called_once_with("Are you sure you want to continue? (y/n) ")
        mock_ChatApplication.return_value.run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
