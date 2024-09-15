import unittest
from unittest.mock import MagicMock, patch
from hermes.chat_models.claude import ClaudeModel
from hermes.chat_models.bedrock import BedrockModel
from hermes.chat_models.gemini import GeminiModel
from hermes.chat_models.openai import OpenAIModel
from hermes.chat_models.ollama import OllamaModel

class TestClaudeModel(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.__getitem__.return_value = {'api_key': 'test_key'}
        self.model = ClaudeModel(self.config, 'claude')

    @patch('anthropic.Anthropic')
    def test_initialize(self, mock_anthropic):
        self.model.initialize()
        mock_anthropic.assert_called_once_with(api_key='test_key')

    @patch('anthropic.Anthropic')
    def test_send_history(self, mock_anthropic):
        self.model.initialize()
        mock_stream = MagicMock()
        mock_stream.text_stream = ['Hello', ' World']
        mock_anthropic.return_value.messages.stream.return_value.__enter__.return_value = mock_stream

        result = list(self.model.send_history([{'role': 'user', 'content': 'Test message'}]))
        self.assertEqual(result, ['Hello', ' World'])

class TestBedrockModel(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.model = BedrockModel(self.config, 'bedrock-claude')

    @patch('boto3.client')
    def test_initialize(self, mock_boto3_client):
        self.model.initialize()
        mock_boto3_client.assert_called_once_with('bedrock-runtime')

    @patch('boto3.client')
    def test_send_history(self, mock_boto3_client):
        self.model.initialize()
        mock_response = {
            'stream': [
                {'contentBlockDelta': {'delta': {'text': 'Hello'}}},
                {'contentBlockDelta': {'delta': {'text': ' World'}}},
                {'messageStop': True}
            ]
        }
        mock_boto3_client.return_value.converse_stream.return_value = mock_response

        result = list(self.model.send_history([{'role': 'user', 'content': 'Test message'}]))
        self.assertEqual(result, ['Hello', ' World'])

class TestGeminiModel(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.__getitem__.return_value = {'api_key': 'test_key'}
        self.model = GeminiModel(self.config, 'gemini')

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_initialize(self, mock_generative_model, mock_configure):
        self.model.initialize()
        mock_configure.assert_called_once_with(api_key='test_key')
        mock_generative_model.assert_called_once_with('gemini-1.5-pro-exp-0801')

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_send_history(self, mock_generative_model, mock_configure):
        self.model.initialize()
        mock_generative_model.return_value.start_chat.return_value.send_message.return_value = [
            MagicMock(text='Hello'),
            MagicMock(text=' World')
        ]

        result = list(self.model.send_history([{'role': 'user', 'content': 'Test message'}]))
        self.assertEqual(result, ['Hello', ' World'])

class TestOpenAIModel(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.__getitem__.return_value = {'api_key': 'test_key'}
        self.model = OpenAIModel(self.config, 'openai')

    @patch('openai.Client')
    def test_initialize(self, mock_client):
        self.model.initialize()
        mock_client.assert_called_once_with(api_key='test_key', base_url='https://api.openai.com/v1')

    @patch('openai.Client')
    def test_send_history(self, mock_client):
        self.model.initialize()
        mock_stream = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content='Hello'))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=' World'))]),
        ]
        mock_client.return_value.chat.completions.create.return_value = iter(mock_stream)

        result = list(self.model.send_history([{'role': 'user', 'content': 'Test message'}]))
        self.assertEqual(result, ['Hello', ' World'])

class TestOllamaModel(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.__getitem__.return_value = {'model': 'llama2'}
        self.model = OllamaModel(self.config, 'ollama')

    def test_initialize(self):
        self.model.initialize()
        self.assertEqual(self.model.model, 'llama2')

    @patch('ollama.chat')
    def test_send_history(self, mock_chat):
        self.model.initialize()
        mock_chat.return_value = [
            {'message': {'content': 'Hello'}},
            {'message': {'content': ' World'}},
        ]

        result = list(self.model.send_history([{'role': 'user', 'content': 'Test message'}]))
        self.assertEqual(result, ['Hello', ' World'])

if __name__ == '__main__':
    unittest.main()
