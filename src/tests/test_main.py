import unittest
from unittest.mock import patch, MagicMock
import configparser
from hermes.main import create_model_and_processors
from hermes.chat_models.claude import ClaudeModel
from hermes.chat_models.bedrock import BedrockModel
from hermes.chat_models.gemini import GeminiModel
from hermes.chat_models.openai import OpenAIModel
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

    def test_unsupported_model(self):
        with self.assertRaises(ValueError):
            create_model_and_processors("unsupported-model", self.config)

if __name__ == '__main__':
    unittest.main()
