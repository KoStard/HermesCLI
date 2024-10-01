import unittest
from unittest.mock import Mock, patch
from hermes.chat_models.gemini import GeminiModel
import google.generativeai as genai

class TestGeminiModel(unittest.TestCase):
    def setUp(self):
        self.config = {
            "api_key": "test_api_key",
            "model_identifier": "gemini/1.5-pro-exp-0827",
            "GEMINI": {}
        }
        self.model = GeminiModel(self.config, "gemini")

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_initialize(self, mock_generative_model, mock_configure):
        self.model.initialize()
        
        mock_configure.assert_called_once_with(api_key="test_api_key")
        mock_generative_model.assert_called_once_with("gemini-1.5-pro-exp-0827")

    @patch('google.generativeai.GenerativeModel')
    def test_send_history(self, mock_generative_model):
        mock_chat = Mock()
        mock_response = Mock()
        mock_response.text = "Hello, world!"
        mock_chat.send_message.return_value = [mock_response]
        mock_generative_model.return_value.start_chat.return_value = mock_chat

        self.model.initialize()
        messages = [{"role": "user", "content": "Hi"}]
        result = list(self.model.send_history(messages))

        self.assertEqual(result, ["Hello, world!"])
        mock_chat.send_message.assert_called_once_with(
            "Hi",
            stream=True,
            safety_settings={
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            }
        )

    def test_get_model_id(self):
        self.assertEqual(self.model.get_model_id('gemini/1.5-pro-exp-0801'), 'gemini-1.5-pro-exp-0801')
        self.assertEqual(self.model.get_model_id('gemini/1.5-pro-exp-0827'), 'gemini-1.5-pro-exp-0827')
        self.assertEqual(self.model.get_model_id('gemini/1.5-pro-002'), 'gemini-1.5-pro-002')
        self.assertEqual(self.model.get_model_id('gemini'), 'gemini-1.5-pro-exp-0827')

if __name__ == '__main__':
    unittest.main()
