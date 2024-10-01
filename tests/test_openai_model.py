import unittest
from unittest.mock import Mock, patch
from hermes.chat_models.openai import OpenAIModel

class TestOpenAIModel(unittest.TestCase):
    def setUp(self):
        self.config = {
            "api_key": "test_api_key",
            "model": "gpt-3.5-turbo"
        }
        self.model = OpenAIModel(self.config, "openai")

    @patch('openai.Client')
    def test_initialize(self, mock_openai):
        self.model.initialize()
        
        mock_openai.assert_called_once_with(api_key="test_api_key", base_url="https://api.openai.com/v1")
        self.assertIsNotNone(self.model.client)
        self.assertEqual(self.model.model, "gpt-3.5-turbo")

    @patch('openai.Client')
    def test_send_history(self, mock_openai):
        mock_client = Mock()
        mock_response = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" world"))]),
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        self.model.initialize()
        messages = [{"role": "user", "content": "Hi"}]
        result = list(self.model.send_history(messages))

        self.assertEqual(result, ["Hello", " world"])
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        )

if __name__ == '__main__':
    unittest.main()
